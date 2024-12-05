# Network API Documentation

## Base URL

/api

## Endpoints

### Posts

#### Get All Posts

GET /api/posts

**Description:**
- Get all non-deleted posts, sorted by creation time in descending order

**Response:**
- Status: 200 OK
json
{
    "message": "Get posts successfully.",
    "posts": [
        {
            // serialized post object
        }
    ]
}

**Error Responses:**
- 400 Bad Request: Data integrity error
- 400 Bad Request: Data validation error 
- 500 Internal Server Error: Database operation error

#### Create New Post

POST /api/posts

**Description:**
- Create a new post

**Authentication:**
- Required

**Request Body:**
json
{
    "content": "string"
}

**Response:**
- Status: 200 OK
json
{
    "message": "Post created successfully."
}

**Error Responses:**
- 400 Bad Request: Empty content
- 400 Bad Request: Invalid JSON format
- 400 Bad Request: Data integrity error
- 400 Bad Request: Data validation error
- 401 Unauthorized: Not logged in
- 500 Internal Server Error: Database operation error

### Single Post Operations

GET /api/posts/<post_id>

🚧 Not implemented yet

### Like Operations

POST /api/posts/<post_id>/like

🚧 Not implemented yet

### Following Posts

GET /api/posts/following

🚧 Not implemented yet