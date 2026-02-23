# Firebase Authentication Integration

## Overview

Your AI Doc Assistant now uses **Firebase Authentication** instead of manual JWT. This means:
- User management is handled by Firebase
- Firebase generates and validates ID tokens
- Your backend validates Firebase tokens for protected endpoints
- No need to manage password hashing yourself

---

## Setup Instructions

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Firebase Setup

#### Step 1: Create a Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a new project"
3. Enter project name (e.g., "AI-Doc-Assistant")
4. Follow the setup wizard

#### Step 2: Enable Authentication
1. In Firebase Console, go to **Authentication**
2. Click **Get Started**
3. Enable **Email/Password**

#### Step 3: Download Service Account Key
1. Go to **Project Settings** (gear icon)
2. Click **Service Accounts** tab
3. Click **Generate New Private Key**
4. Save the JSON file as **`firebase-key.json`** in your project root

#### Step 4: Update `.env` File
```
FIREBASE_CREDENTIALS_PATH=firebase-key.json
FIREBASE_PROJECT_ID=your-firebase-project-id
```

Find `FIREBASE_PROJECT_ID` in the downloaded JSON file (look for `"project_id"`).

### 3. Database Setup

Your PostgreSQL `app_records` table is used to store application-specific user data:

```sql
-- app_records table already created with:
-- - record_type: 'user' for user records
-- - owner_uid: Firebase UID
-- - meta: JSON storing email, display_name, etc.
```

---

## API Endpoints

### Authentication Endpoints

#### 1. Register a New User
**Endpoint**: `POST /auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "display_name": "John Doe"
}
```

**Response**:
```json
{
  "message": "User registered successfully. Use Firebase SDK to authenticate.",
  "user": {
    "uid": "firebase-uid-here",
    "email": "user@example.com",
    "display_name": "John Doe"
  }
}
```

**Note**: Registration creates a Firebase user. To actually authenticate, client must use Firebase SDK.

#### 2. Get Current User Info
**Endpoint**: `GET /auth/me`

**Headers**:
```
Authorization: Bearer <firebase-id-token>
```

**Response**:
```json
{
  "uid": "firebase-uid",
  "email": "user@example.com",
  "display_name": "John Doe",
  "email_verified": true
}
```

#### 3. Verify Firebase Token
**Endpoint**: `POST /auth/verify-token`

**Request Body**:
```json
{
  "token": "eyJhbGc..."
}
```

**Response**:
```json
{
  "valid": true,
  "user": {
    "uid": "firebase-uid",
    "email": "user@example.com",
    "email_verified": true,
    "name": "John Doe"
  }
}
```

---

## How to Use with Firebase SDK

### JavaScript/Web Client

```javascript
// 1. Install Firebase SDK
// npm install firebase

// 2. Initialize Firebase in your app
import { initializeApp } from "firebase/app";
import { getAuth, signUp, signIn, signOut } from "firebase/auth";

const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-firebase-project-id",
  // ... other config
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// 3. Register User
import { createUserWithEmailAndPassword } from "firebase/auth";

async function registerUser(email, password) {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    
    // Also register in your backend
    await fetch("http://localhost:8000/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: user.email,
        password: password,
        display_name: user.displayName
      })
    });
    
    return user;
  } catch (error) {
    console.error("Registration failed:", error);
  }
}

// 4. Login User
import { signInWithEmailAndPassword } from "firebase/auth";

async function loginUser(email, password) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    return userCredential.user;
  } catch (error) {
    console.error("Login failed:", error);
  }
}

// 5. Get ID Token for API Calls
async function getIdToken() {
  const user = auth.currentUser;
  if (user) {
    return await user.getIdToken();
  }
  return null;
}

// 6. Call Protected Backend Endpoint
async function askQuestion(question) {
  const token = await getIdToken();
  
  const response = await fetch("http://localhost:8000/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ input: question })
  });
  
  return await response.json();
}

// 7. Logout
async function logoutUser() {
  await signOut(auth);
}
```

### Python Client

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Note: Firebase SDK for Python is limited
# For client-side auth, use JavaScript/Web SDK
# For backend service accounts, use firebase-admin

# If using firebase-admin in Python:
import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

# Create custom token for testing
custom_token = auth.create_custom_token("user-uid")
print(f"Custom token: {custom_token}")

# Use ID token to call your API
headers = {"Authorization": f"Bearer {id_token}"}
response = requests.post(
    f"{BASE_URL}/ask",
    json={"input": "What is AI?"},
    headers=headers
)
print(response.json())
```

---

## How Authentication Works

### Registration Flow
```
1. User submits email + password → Firebase SDK
2. Firebase creates user account
3. Client calls your backend /auth/register endpoint
4. Backend creates app_records entry with Firebase UID
5. Backend returns user info
```

### Authentication Flow
```
1. User provides email + password → Firebase SDK
2. Firebase verifies credentials
3. Firebase returns ID token (auto-expires in 1 hour)
4. Client stores token (localStorage, etc.)
5. Client sends token in Authorization header
```

### API Request Flow
```
1. Client sends: Authorization: Bearer <firebase-id-token>
2. Backend receives request
3. Backend calls Firebase to verify token
4. Firebase returns user info if valid
5. Backend processes request with user context
6. Backend returns response
```

---

## User Data Storage

### Firebase (Managed by Firebase)
- UID
- Email
- Password (hashed by Firebase)
- Display name
- Email verification status
- Last login time
- Creation date

### PostgreSQL (Your app_records table)
```json
{
  "id": "firebase-uid-same-as-uid",
  "record_type": "user",
  "owner_uid": "firebase-uid",
  "meta": {
    "email": "user@example.com",
    "display_name": "John Doe",
    "firebase_uid": "firebase-uid"
  },
  "created_at": "2026-02-23T10:00:00Z"
}
```

---

## Protected Endpoints

All endpoints that use `get_current_user` dependency require a valid Firebase ID token:

```python
from app.core.dependencies import get_current_user

@router.post("/my-endpoint")
def my_endpoint(current_user: dict = Depends(get_current_user)):
    # current_user contains: {"uid": "...", "email": "...", "name": "..."}
    user_uid = current_user["uid"]
    return {"user_uid": user_uid}
```

Currently protected:
- `GET /auth/me`
- `POST /ask`

---

## Testing with Swagger UI

### Option 1: Manual Token Generation (Python)
```python
from firebase_admin import auth

# Generate a custom token
custom_token = auth.create_custom_token("test-user-uid")
print(custom_token)

# Copy the token and paste in Swagger UI
```

### Option 2: Use JavaScript Console
```javascript
// In browser console after logging in via Firebase SDK
firebase.auth().currentUser.getIdToken().then(token => {
  console.log(token);
  // Copy this token to Swagger UI
});
```

### Steps:
1. Generate a token (see options above)
2. Go to http://localhost:8000/docs
3. Click "Authorize" button
4. Enter: `Bearer <your-firebase-id-token>`
5. Test endpoints

---

## Security Features

✅ **Firebase Handles**:
- Secure password storage
- Email verification
- Session management
- Token generation and rotation
- Multi-factor authentication (if enabled)

✅ **Your Backend**:
- Validates every token
- Associates user UID with app data
- Enforces authorization rules
- Logs user activities

---

## Environment Variables

```bash
# Firebase
FIREBASE_CREDENTIALS_PATH=firebase-key.json          # Path to service account JSON
FIREBASE_PROJECT_ID=your-firebase-project-id        # Firebase project ID

# Database
DATABASE_URL=postgresql://...
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_doc_assistant
DB_USER=username
DB_PASSWORD=password

# Application
APP_NAME=AI Document Assistant
APP_HOST=127.0.0.1
APP_PORT=8000
GEMINI_API_KEY=your-key
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'firebase_admin'"
```bash
pip install firebase-admin
pip install -r requirements.txt
```

### "Invalid credential path"
- Ensure `firebase-key.json` is in project root
- Check `FIREBASE_CREDENTIALS_PATH` in `.env`

### "Invalid token"
- Token may be expired (re-authenticate)
- May be from different Firebase project
- Check token is in `Bearer <token>` format

### "User not found in database"
- User was created in Firebase but not in PostgreSQL
- Call `/auth/register` after Firebase registration

---

## Next Steps

1. ✅ Setup Firebase Console
2. ✅ Download service account key
3. ✅ Update `.env` with Firebase config
4. ✅ Install dependencies
5. ✅ Start backend: `uvicorn main:app --reload`
6. ✅ Integrate Firebase SDK in frontend
7. ✅ Test authentication flow

Enjoy Firebase authentication! 🔐
