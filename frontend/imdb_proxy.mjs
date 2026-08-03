import { createServer } from 'http';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

const PORT = 3031;
const GRAPHQL_URL = 'https://graphql.imdb.com/';

function loadCredentials() {
  const envPath = join(process.cwd(), '.env');
  if (!existsSync(envPath)) return null;
  
  const envContent = readFileSync(envPath, 'utf-8');
  const env = {};
  envContent.split('\n').forEach(line => {
    const [key, ...value] = line.split('=');
    if (key && value.length) env[key.trim()] = value.join('=').trim();
  });
  return env;
}

function buildCookieString(env) {
  const parts = [];
  if (env.IMDB_SESSION_ID) parts.push(`session-id=${env.IMDB_SESSION_ID}`);
  if (env.IMDB_UBID_MAIN) parts.push(`ubid-main=${env.IMDB_UBID_MAIN}`);
  parts.push('lc-main=en_US');
  if (env.IMDB_X_MAIN) parts.push(`x-main=${env.IMDB_X_MAIN}`);
  if (env.IMDB_AT_MAIN) parts.push(`at-main=${env.IMDB_AT_MAIN}`);
  if (env.IMDB_SESS_AT_MAIN) parts.push(`sess-at-main=${env.IMDB_SESS_AT_MAIN}`);
  parts.push('session-id-time=2082787201l');
  if (env.IMDB_SESSION_TOKEN) parts.push(`session-token=${env.IMDB_SESSION_TOKEN}`);
  return parts.join('; ');
}

async function handleGraphQL(req, res) {
  let body = '';
  for await (const chunk of req) body += chunk;
  
  const env = loadCredentials();
  if (!env) {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'No .env file found' }));
    return;
  }

  const { query, variables, operationName } = JSON.parse(body);
  
  try {
    const response = await fetch(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': buildCookieString(env),
        'x-imdb-client-language': 'en-US',
        'x-imdb-user-language': 'en-US',
      },
      body: JSON.stringify({ query, variables, operationName }),
    });

    const data = await response.json();
    res.writeHead(response.status, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(data));
  } catch (error) {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: error.message }));
  }
}

const server = createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.url === '/graphql' && req.method === 'POST') {
    await handleGraphQL(req, res);
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});

server.listen(PORT, () => {
  console.log(`IMDb proxy running on http://localhost:${PORT}`);
});
