"""
IMDb GraphQL Operations - Known persisted query hashes.
"""

# Query Operations (Read)
OPERATIONS = {
    # User Lists
    "YourListsSidebar": {
        "hash": "7e9a98408bca0450bffb02fbafc807ad32295ff4839bc6c3a5669c3afcb6a2da",
        "description": "Fetch user's custom lists",
    },
    # User Ratings & Watched Status
    "PersonalizedUserData": {
        "hash": "7c4e0771d67f21fc27fd44fc46d49cc589225a9c5e63e51cc0b8d42f39ee99cc",
        "description": "Get user's ratings and watched status for titles",
    },
    # Recently Viewed Items
    "RVI_Items": {
        "hash": "32eda43bfa1053f69036b945638fc4a0ae6cc4a2429de224b3185f8b0e37717b",
        "description": "Get recently viewed titles",
    },
}

# Mutation Operations (Write)
MUTATIONS = {
    # List Management
    "createList": "createList",
    "addItemToList": "addItemToList",
    "removeElementFromList": "removeElementFromList",
    "editListName": "editListName",
    "editListDescription": "editListDescription",
    "editListVisibility": "editListVisibility",
    "deleteList": "deleteList",
    "copyListItemIds": "copyListItemIds",
    
    # Ratings
    "rateTitle": "rateTitle",
    "deleteTitleRating": "deleteTitleRating",
    
    # Watchlist (Predefined List)
    "addItemToPredefinedList": "addItemToPredefinedList",
    "removeElementFromPredefinedList": "removeElementFromPredefinedList",
    
    # Recently Viewed
    "addToRecentlyViewedItems": "addToRecentlyViewedItems",
    "clearRecentlyViewed": "clearRecentlyViewed",
}

# GraphQL Query Strings (for mutations)
QUERIES = {
    "createList": """
    mutation CreateList($input: CreateListInput!) {
        createList(input: $input) {
            listId
        }
    }
    """,
    "addItemToList": """
    mutation AddItemToList($input: AddItemToListInput!) {
        addItemToList(input: $input) {
            listId
        }
    }
    """,
    "removeElementFromList": """
    mutation RemoveElementFromList($listId: ID!, $itemId: ID!) {
        removeElementFromList(listId: $listId, itemId: $itemId) {
            listId
        }
    }
    """,
    "rateTitle": """
    mutation RateTitle($titleId: ID!, $rating: Int!) {
        rateTitle(titleId: $titleId, rating: $rating) {
            rating {
                value
            }
        }
    }
    """,
    "deleteTitleRating": """
    mutation DeleteTitleRating($titleId: ID!) {
        deleteTitleRating(titleId: $titleId)
    }
    """,
    "addItemToPredefinedList": """
    mutation AddItemToPredefinedList($listType: PredefinedListType!, $itemId: ID!, $itemType: String!) {
        addItemToPredefinedList(listType: $listType, itemId: $itemId, itemType: $itemType) {
            listId
        }
    }
    """,
    "removeElementFromPredefinedList": """
    mutation RemoveElementFromPredefinedList($listType: PredefinedListType!, $itemId: ID!) {
        removeElementFromPredefinedList(listType: $listType, itemId: $itemId) {
            listId
        }
    }
    """,
    "editListName": """
    mutation EditListName($listId: ID!, $name: String!) {
        editListName(listId: $listId, name: $name) {
            listId
        }
    }
    """,
    "editListVisibility": """
    mutation EditListVisibility($listId: ID!, $visibility: ListVisibility!) {
        editListVisibility(listId: $listId, visibility: $visibility) {
            listId
        }
    }
    """,
    "deleteList": """
    mutation DeleteList($listId: ID!) {
        deleteList(listId: $listId)
    }
    """,
}
