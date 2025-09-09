# FloatChat ARGO API Documentation

## Overview

The FloatChat ARGO REST API provides programmatic access to oceanographic data, user management, and AI-powered chat functionality.

**Base URL**: `http://localhost:5000/api`  
**Authentication**: JWT Bearer Token  
**Content-Type**: `application/json`

## Authentication

### Login
```http
POST /api/login
Content-Type: application/json

{
    "username": "user",
    "password": "user123"  
}
```

**Response**:
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 2,
        "username": "user", 
        "role": "user",
        "full_name": "Marine Researcher"
    }
}
```

### Register
```http
POST /api/register
Content-Type: application/json

{
    "username": "newuser",
    "email": "user@example.com",
    "password": "password123",
    "full_name": "New User"
}
```

## ARGO Float Data

### Get All Floats
```http
GET /api/floats
Authorization: Bearer <token>
```

**Response**:
```json
[
    {
        "id": 1,
        "float_id": "2901623",
        "latitude": -10.5,
        "longitude": 67.8,
        "status": "active",
        "deployment_date": "2023-03-15",
        "region": "Indian Ocean",
        "battery_level": 87,
        "data_quality": "good"
    }
]
```

### Add Float (Admin Only)
```http
POST /api/floats
Authorization: Bearer <admin_token>
Content-Type: application/json

{
    "float_id": "2901628",
    "latitude": -14.2,
    "longitude": 69.5,
    "status": "active",
    "region": "Indian Ocean"
}
```

### Get Float Profiles
```http
GET /api/profiles/2901623
Authorization: Bearer <token>
```

**Response**:
```json
[
    {
        "id": 1,
        "profile_date": "2024-09-01T12:00:00",
        "latitude": -10.52,
        "longitude": 67.83,
        "depth": 5,
        "temperature": 28.5,
        "salinity": 35.1,
        "pressure": 5.1,
        "oxygen": 215.4
    }
]
```

## Chat System

### Send Chat Message
```http
POST /api/chat
Authorization: Bearer <token>
Content-Type: application/json

{
    "message": "Show me temperature profiles near the equator"
}
```

**Response**:
```json
{
    "response": "I found 12 ARGO float profiles near the equator with average surface temperature of 28.2°C...",
    "sources": [
        {
            "text": "Temperature profiles show oceanic thermal structure",
            "metadata": {"topic": "temperature"},
            "distance": 0.23
        }
    ]
}
```

## Admin Endpoints

### Convert NetCDF Files
```http
POST /api/admin/convert-nc
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data

file: <netcdf_file>
```

**Response**:
```json
{
    "message": "File converted successfully",
    "csv_file": "R2901623_001.csv",
    "rows": 2048,
    "columns": 12
}
```

### Update Chatbot Training
```http
POST /api/admin/chatbot-training
Authorization: Bearer <admin_token>
Content-Type: application/json

{
    "training_data": [
        {
            "question": "What is temperature?",
            "answer": "Temperature is a measure of thermal energy in ocean water",
            "category": "oceanography"
        }
    ]
}
```

### System Status
```http
GET /api/admin/system-status
Authorization: Bearer <admin_token>
```

**Response**:
```json
{
    "database": {
        "total_floats": 5,
        "active_floats": 4,
        "total_users": 2,
        "total_profiles": 10
    },
    "mongodb": {
        "chat_logs": 25,
        "conversions": 3,
        "vector_db_size": 4
    },
    "system": {
        "uptime": "99.9%",
        "last_update": "2024-09-09T10:00:00Z"
    }
}
```

## Error Responses

### Authentication Error
```json
{
    "error": "Token is missing",
    "status": 401
}
```

### Authorization Error
```json
{
    "error": "Admin access required",
    "status": 403
}
```

### Validation Error
```json
{
    "error": "Username and password required",
    "status": 400
}
```

## Rate Limits

- **General API**: 1000 requests per hour per user
- **Chat API**: 100 requests per hour per user  
- **File Upload**: 10 requests per hour per admin

## WebSocket Events (Future)

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:5000/ws');

// Real-time float updates
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'float_update') {
        updateFloatStatus(data.float_id, data.status);
    }
};
```

## SDKs and Examples

### Python Client
```python
import requests

class FloatChatClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.token = None

    def login(self, username, password):
        response = requests.post(f"{self.base_url}/login", json={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
            return True
        return False

    def get_floats(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/floats", headers=headers)
        return response.json()

    def chat(self, message):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/chat", 
                               headers=headers, 
                               json={"message": message})
        return response.json()

# Usage
client = FloatChatClient()
client.login("user", "user123")
floats = client.get_floats()
response = client.chat("Show temperature data")
```

### JavaScript Client
```javascript
class FloatChatAPI {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
        this.token = null;
    }

    async login(username, password) {
        const response = await fetch(`${this.baseURL}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });

        if (response.ok) {
            const data = await response.json();
            this.token = data.token;
            return data;
        }
        throw new Error('Login failed');
    }

    async getFloats() {
        const response = await fetch(`${this.baseURL}/floats`, {
            headers: {'Authorization': `Bearer ${this.token}`}
        });
        return response.json();
    }

    async sendMessage(message) {
        const response = await fetch(`${this.baseURL}/chat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({message})
        });
        return response.json();
    }
}

// Usage
const api = new FloatChatAPI();
await api.login('user', 'user123');
const floats = await api.getFloats();
const response = await api.sendMessage('Show salinity profiles');
```

## Changelog

### v1.0.0 (2024-09-09)
- Initial API release
- Authentication and user management
- ARGO float CRUD operations
- Chat system with vector search
- Admin file conversion tools
- MongoDB logging system

For more examples and detailed documentation, visit our [GitHub repository](https://github.com/your-repo/floatchat-argo).
