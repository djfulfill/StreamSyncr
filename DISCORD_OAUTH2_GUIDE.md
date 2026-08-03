# Discord OAuth2 Integration — Developer Guide

## Overview

Add "Connect Discord" to WeTrakr so users can link their Discord accounts. This uses OAuth2 Authorization Code Grant — the standard secure flow for server-side apps.

**What we're building:**
- User clicks "Connect Discord" → redirected to Discord → authorizes → redirected back → accounts linked
- WeTrakr stores Discord user ID, username, and avatar
- User can disconnect anytime

---

## Step 1: Create Discord Application

1. Go to https://discord.com/developers/applications
2. Click **New Application** → name it `WeTrakr` → Create
3. Go to **OAuth2** section
4. Copy the **Client ID** and **Client Secret**
5. Add **Redirect URI:** `https://wetrakr.com/integrations/discord/callback`
6. Click **Save Changes**

**Scopes needed:** `identify` (gets user ID, username, avatar)

---

## Step 2: Environment Variables

Add to your `.env` or secrets manager:

```env
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here
DISCORD_REDIRECT_URI=https://wetrakr.com/integrations/discord/callback
```

---

## Step 3: Database Schema

Add a `linked_accounts` table (or extend existing integrations table):

```sql
CREATE TABLE linked_accounts (
    _id ObjectId PRIMARY KEY,
    user_id ObjectId NOT NULL REFERENCES users(_id),
    provider VARCHAR(20) NOT NULL,          -- 'discord', 'trakt', etc.
    provider_user_id VARCHAR(100) NOT NULL,  -- Discord's user ID
    username VARCHAR(100),                   -- Discord username
    avatar_url VARCHAR(500),                 -- Discord avatar
    access_token VARCHAR(500),               -- OAuth access token
    refresh_token VARCHAR(500),              -- OAuth refresh token
    token_expires_at Date,                   -- When access token expires
    linked_at Date DEFAULT Date.now,
    UNIQUE(user_id, provider)               -- One Discord per WeTrakr account
);

CREATE INDEX idx_linked_accounts_user ON linked_accounts(user_id);
CREATE INDEX idx_linked_accounts_provider ON linked_accounts(provider, provider_user_id);
```

---

## Step 4: API Endpoints

### 4.1 Check Connection Status

```javascript
// GET /proxy/integrations/discord
// Requires: authenticated user (JWT)

async function getDiscordStatus(req, res) {
    const userId = req.user.id;
    
    const account = await db.collection('linked_accounts').findOne({
        user_id: userId,
        provider: 'discord'
    });
    
    if (!account) {
        return res.json({ provider: 'discord', connected: false, data: null });
    }
    
    return res.json({
        provider: 'discord',
        connected: true,
        data: {
            discord_user_id: account.provider_user_id,
            username: account.username,
            avatar: account.avatar_url,
            linked_at: account.linked_at
        }
    });
}
```

### 4.2 Get Authorization URL

```javascript
// GET /proxy/integrations/discord/connect
// Requires: authenticated user (JWT)
// Returns: Discord OAuth2 authorize URL with CSRF state

import crypto from 'crypto';

async function getDiscordConnectUrl(req, res) {
    const userId = req.user.id;
    
    // Generate CSRF state token
    const state = crypto.randomBytes(32).toString('hex');
    
    // Store state with user ID (expires in 10 mins)
    await db.collection('oauth_states').insertOne({
        user_id: userId,
        provider: 'discord',
        state: state,
        expires_at: new Date(Date.now() + 10 * 60 * 1000)
    });
    
    const params = new URLSearchParams({
        response_type: 'code',
        client_id: process.env.DISCORD_CLIENT_ID,
        scope: 'identify',
        redirect_uri: process.env.DISCORD_REDIRECT_URI,
        state: state
    });
    
    return res.json({
        url: `https://discord.com/oauth2/authorize?${params.toString()}`
    });
}
```

### 4.3 Handle Callback (Link Account)

```javascript
// POST /proxy/integrations/discord/callback
// Requires: authenticated user (JWT)
// Body: { code: "auth_code_from_discord", state: "csrf_token" }

async function handleDiscordCallback(req, res) {
    const userId = req.user.id;
    const { code, state } = req.body;
    
    // 1. Verify CSRF state
    const stateRecord = await db.collection('oauth_states').findOneAndDelete({
        user_id: userId,
        provider: 'discord',
        state: state,
        expires_at: { $gt: new Date() }
    });
    
    if (!stateRecord) {
        return res.status(400).json({ error: 'Invalid or expired state token' });
    }
    
    // 2. Exchange code for tokens
    const tokenResponse = await fetch('https://discord.com/api/oauth2/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
            grant_type: 'authorization_code',
            code: code,
            redirect_uri: process.env.DISCORD_REDIRECT_URI
        }),
        // Discord requires Basic auth with client_id:client_secret
        headers: {
            'Authorization': `Basic ${Buffer.from(
                `${process.env.DISCORD_CLIENT_ID}:${process.env.DISCORD_CLIENT_SECRET}`
            ).toString('base64')}`
        }
    });
    
    const tokens = await tokenResponse.json();
    
    if (tokens.error) {
        return res.status(400).json({ error: 'Failed to exchange code', details: tokens });
    }
    
    // 3. Get Discord user info
    const userResponse = await fetch('https://discord.com/api/users/@me', {
        headers: {
            'Authorization': `Bearer ${tokens.access_token}`
        }
    });
    
    const discordUser = await userResponse.json();
    
    if (discordUser.code) {
        return res.status(400).json({ error: 'Failed to fetch Discord user', details: discordUser });
    }
    
    // 4. Store/update linked account
    await db.collection('linked_accounts').updateOne(
        { user_id: userId, provider: 'discord' },
        {
            $set: {
                provider_user_id: discordUser.id,
                username: discordUser.username,
                avatar_url: discordUser.avatar 
                    ? `https://cdn.discordapp.com/avatars/${discordUser.id}/${discordUser.avatar}.png`
                    : null,
                access_token: tokens.access_token,
                refresh_token: tokens.refresh_token,
                token_expires_at: new Date(Date.now() + tokens.expires_in * 1000),
                linked_at: new Date()
            }
        },
        { upsert: true }
    );
    
    // 5. Return success
    return res.json({
        provider: 'discord',
        connected: true,
        data: {
            discord_user_id: discordUser.id,
            username: discordUser.username,
            avatar: discordUser.avatar 
                ? `https://cdn.discordapp.com/avatars/${discordUser.id}/${discordUser.avatar}.png`
                : null
        }
    });
}
```

### 4.4 Disconnect Discord

```javascript
// DELETE /proxy/integrations/discord
// Requires: authenticated user (JWT)

async function disconnectDiscord(req, res) {
    const userId = req.user.id;
    
    await db.collection('linked_accounts').deleteOne({
        user_id: userId,
        provider: 'discord'
    });
    
    return res.json({ provider: 'discord', connected: false });
}
```

---

## Step 5: Token Refresh (Background Job)

Discord access tokens expire after 7 days. Add a cron job to refresh them:

```javascript
// Run daily
async function refreshDiscordTokens() {
    const expiredAccounts = await db.collection('linked_accounts').find({
        provider: 'discord',
        token_expires_at: { $lt: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000) } // 2 days before expiry
    }).toArray();
    
    for (const account of expiredAccounts) {
        try {
            const response = await fetch('https://discord.com/api/oauth2/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': `Basic ${Buffer.from(
                        `${process.env.DISCORD_CLIENT_ID}:${process.env.DISCORD_CLIENT_SECRET}`
                    ).toString('base64')}`
                },
                body: new URLSearchParams({
                    grant_type: 'refresh_token',
                    refresh_token: account.refresh_token
                })
            });
            
            const tokens = await response.json();
            
            if (tokens.access_token) {
                await db.collection('linked_accounts').updateOne(
                    { _id: account._id },
                    {
                        $set: {
                            access_token: tokens.access_token,
                            refresh_token: tokens.refresh_token,
                            token_expires_at: new Date(Date.now() + tokens.expires_in * 1000)
                        }
                    }
                );
                console.log(`Refreshed Discord token for user ${account.user_id}`);
            } else {
                console.error(`Failed to refresh token for user ${account.user_id}:`, tokens);
                // Token might be revoked — could disconnect or flag for re-auth
            }
        } catch (err) {
            console.error(`Error refreshing Discord token for user ${account.user_id}:`, err);
        }
    }
}
```

---

## Step 6: Frontend (Settings Page)

Add to Settings → Integrations:

```jsx
// DiscordConnection.jsx
function DiscordConnection({ status, onConnect, onDisconnect }) {
    return (
        <div className="integration-item">
            <div className="integration-info">
                <img src="/discord-icon.svg" alt="Discord" />
                <div>
                    <h3>Discord</h3>
                    {status.connected ? (
                        <p className="connected">
                            Connected as <strong>{status.data.username}</strong>
                        </p>
                    ) : (
                        <p>Connect your Discord account</p>
                    )}
                </div>
            </div>
            
            {status.connected ? (
                <button onClick={onDisconnect} className="btn-disconnect">
                    Disconnect
                </button>
            ) : (
                <button onClick={onConnect} className="btn-connect">
                    Connect Discord
                </button>
            )}
        </div>
    );
}
```

```jsx
// Usage in Integrations page
function IntegrationsPage() {
    const [discordStatus, setDiscordStatus] = useState(null);
    
    useEffect(() => {
        fetch('/proxy/integrations/discord')
            .then(r => r.json())
            .then(setDiscordStatus);
    }, []);
    
    const handleConnect = async () => {
        const { url } = await fetch('/proxy/integrations/discord/connect')
            .then(r => r.json());
        window.location.href = url; // Redirect to Discord
    };
    
    const handleDisconnect = async () => {
        await fetch('/proxy/integrations/discord', { method: 'DELETE' });
        setDiscordStatus({ provider: 'discord', connected: false, data: null });
    };
    
    // Handle callback redirect (when user returns from Discord)
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');
        const state = params.get('state');
        
        if (code && state) {
            fetch('/proxy/integrations/discord/callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, state })
            })
            .then(r => r.json())
            .then(setDiscordStatus)
            .then(() => {
                // Clean up URL
                window.history.replaceState({}, '', '/settings/integrations');
            });
        }
    }, []);
    
    if (!discordStatus) return <Loading />;
    
    return (
        <div>
            <h2>Integrations</h2>
            <DiscordConnection 
                status={discordStatus}
                onConnect={handleConnect}
                onDisconnect={handleDisconnect}
            />
        </div>
    );
}
```

---

## Security Checklist

- [ ] CSRF state token is random (32 bytes), stored per-user, expires in 10 mins
- [ ] State is verified on callback and deleted after use (single use)
- [ ] Redirect URI is exactly `https://wetrakr.com/integrations/discord/callback` (no trailing slash)
- [ ] Tokens are encrypted at rest (or use a secrets manager)
- [ ] Client secret is never exposed to frontend
- [ ] Token refresh runs server-side only
- [ ] Rate limit the callback endpoint (prevent brute force)

---

## Testing

1. **Local testing:** Use `http://localhost:3000/integrations/discord/callback` as redirect URI in Discord dev portal
2. **Check status:** `GET /proxy/integrations/discord` → should return `{connected: false}`
3. **Connect flow:** Click Connect → Discord auth page → authorize → redirect back → `{connected: true}`
4. **Disconnect:** `DELETE /proxy/integrations/discord` → `{connected: false}`
5. **Token refresh:** Wait 7 days (or mock time) → verify tokens refresh automatically
6. **Edge cases:** Revoke Discord app access → verify graceful handling

---

## Discord API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/oauth2/authorize` | GET | User authorization page |
| `/api/oauth2/token` | POST | Exchange code / refresh token |
| `/api/oauth2/token/revoke` | POST | Revoke token (on disconnect) |
| `/api/users/@me` | GET | Get authenticated user's info |

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `.env` | Add `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI` |
| `models/linkedAccounts.js` | New model for linked_accounts collection |
| `routes/integrations.js` | New route file for integration endpoints |
| `controllers/discord.js` | New controller with OAuth logic |
| `jobs/refreshTokens.js` | Add Discord token refresh to existing cron |
| `frontend/settings/Integrations.jsx` | Add Discord connection UI |

---

*Created: 2026-08-02*
*Author: Philip (user)*
