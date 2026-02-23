# JWT Authentication Documentation

## Overview
JWT (JSON Web Token) authentication has been successfully integrated into your AI Doc Assistant application. Users must register and login to access protected endpoints.

## Setup Instructions

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file from `.env.example`:
```powershell
cp .env.example .env
```

**Important**: Update the `SECRET_KEY` in `.env` with a secure random key:
```powershell
# Generate a secure secret key using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

Add the generated key to your `.env` file:
```
SECRET_KEY=your-generated-secret-key-here
```

### 3. Database Setup
Ensure your PostgreSQL database has the schema from your SQL script already applied.

## API Endpoints

### Authentication Endpoints

#### 1. Register a New User
**Endpoint**: `POST /auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "secure_password123",
  "full_name": "John Doe"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

#### 2. Login
**Endpoint**: `POST /auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "secure_password123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

#### 3. Get Current User Info
**Endpoint**: `GET /auth/me`

**Headers**: 
```
Authorization: Bearer <your-access-token>
```

**Response**:
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2026-02-23T10:30:00+00:00"
}
```

### Protected Endpoints

#### Ask Endpoint (Now Protected)
**Endpoint**: `POST /ask`

**Headers**: 
```
Authorization: Bearer <your-access-token>
```

**Request Body**:
```json
{
  "input": "Your question here"
}
```

**Response**:
```json
{
  "model": "gemini-2.0-flash",
  "answer": "AI response here",
  "user_id": "uuid-of-authenticated-user"
}
```

## Usage Examples

### Using cURL

#### Register:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

#### Login:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

#### Use Protected Endpoint:
```bash
# Replace YOUR_TOKEN with the access_token from login response
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "input": "What is artificial intelligence?"
  }'
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Register
response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
})
token = response.json()["access_token"]

# Use protected endpoint
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{BASE_URL}/ask",
    json={"input": "What is machine learning?"},
    headers=headers
)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
const BASE_URL = "http://localhost:8000";

// Register and login
async function authenticate() {
  const response = await fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'test@example.com',
      password: 'password123',
      full_name: 'Test User'
    })
  });
  const data = await response.json();
  return data.access_token;
}

// Use protected endpoint
async function askQuestion(token, question) {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ input: question })
  });
  return await response.json();
}

// Usage
const token = await authenticate();
const result = await askQuestion(token, "What is AI?");
console.log(result);
```

## Database Schema

The authentication system uses your existing `app_records` table:

- Users are stored with `record_type = 'user'`
- User data is stored in the `meta` JSONB field:
  - `email`: User's email address
  - `full_name`: User's full name
  - `password_hash`: Bcrypt hashed password
- `owner_uid`: For user records, this is set to their own `id`

## Security Features

1. **Password Hashing**: Uses bcrypt for secure password storage
2. **JWT Tokens**: Tokens expire after 30 minutes (configurable)
3. **Bearer Token Authentication**: Standard HTTP Bearer authentication
4. **Protected Routes**: All sensitive endpoints require valid JWT tokens
5. **User Isolation**: Each user's `owner_uid` is embedded in the token for data isolation

## Configuration Options

Edit these in your `.env` file:

- `SECRET_KEY`: Secret key for JWT signing (REQUIRED - must be secure!)
- `JWT_ALGORITHM`: Algorithm for JWT (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30 minutes)

## Testing with Swagger UI

1. Start your server:
   ```powershell
   uvicorn main:app --reload
   ```

2. Open http://localhost:8000/docs

3. Register a new user using `/auth/register`

4. Copy the `access_token` from the response

5. Click the "Authorize" button at the top of Swagger UI

6. Enter: `Bearer <your-access-token>`

7. Now you can test all protected endpoints!

## Notes

- The `/` and `/db-test` endpoints remain public (health checks)
- The `/models` endpoint remains public
- The `/ask` endpoint now requires authentication
- Tokens are stateless (no database lookup needed for validation)
- Add authentication to more routes by importing `get_current_user` dependency

## Adding Authentication to Other Routes

To protect any route, add the `current_user` dependency:

```python
from fastapi import Depends
from app.core.dependencies import get_current_user

@router.get("/my-protected-route")
def my_route(current_user: dict = Depends(get_current_user)):
    # current_user contains: {"owner_uid": "...", "email": "..."}
    return {"message": f"Hello {current_user['email']}"}
```
