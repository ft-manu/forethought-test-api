# Test API - Comprehensive RESTful API Documentation

## 🚀 Overview
This is a **production-ready RESTful API** built with Flask that provides comprehensive CRUD operations for organizations, users, and profiles. The API features advanced validation, caching, rate limiting, batch operations, OpenAPI documentation, and enterprise-grade security.

## 📋 Table of Contents
1. [Features](#-features)
2. [Prerequisites](#-prerequisites)
3. [Quick Start](#-quick-start)
4. [Project Structure](#-project-structure)
5. [API Documentation](#-api-documentation)
6. [Authentication & Security](#-authentication--security)
7. [Endpoints Reference](#-endpoints-reference)
8. [Validation & Error Handling](#-validation--error-handling)
9. [Advanced Features](#-advanced-features)
10. [Testing](#-testing)
11. [Deployment](#-deployment)
12. [Troubleshooting](#-troubleshooting)

## ✨ Features

### 🔧 Core Features
- **RESTful API Design** - Full CRUD operations following REST principles
- **OpenAPI 3.0 Specification** - Complete API documentation with Swagger UI
- **Bearer Token Authentication** - Secure API access with token validation
- **Comprehensive Validation** - Input validation with detailed error messages
- **Rate Limiting** - Protection against abuse with configurable limits
- **Caching** - Intelligent caching for improved performance
- **Batch Operations** - Bulk create/update/delete operations
- **Advanced Search** - Multi-entity search with filtering
- **Pagination** - Efficient data retrieval with pagination support
- **Error Handling** - Consistent error responses with proper HTTP status codes

### 🛡️ Security Features
- **Bearer Token Authentication** - Static token: `ft_test_api_2024`
- **Input Validation** - Comprehensive data validation and sanitization
- **Rate Limiting** - Per-endpoint rate limiting (10-100 requests/minute)
- **CORS Support** - Cross-origin resource sharing configuration
- **Request Compression** - Gzip compression for improved performance

### 📊 Data Management
- **Organizations** - Company/organization management with type classification
- **Users** - User management with email uniqueness and organization relationships
- **Profiles** - User profile management with nested settings and preferences
- **Relationships** - Automatic relationship management between entities

### 🔍 Advanced Capabilities
- **Duplicate Prevention** - ID and email uniqueness validation
- **Auto-generation** - Safe ID generation with conflict resolution
- **Batch Processing** - Up to 50 operations per batch request
- **Multi-entity Search** - Search across organizations, users, and profiles
- **Flexible Filtering** - Query parameter-based filtering on any field
- **Statistics** - Real-time statistics and analytics endpoints

## 🔧 Prerequisites
- **Python 3.8+** - Required for Flask and modern Python features
- **pip** - Python package manager
- **ngrok** (optional) - For public API exposure
- **curl** or **Postman** - For API testing

## 🚀 Quick Start

### 1. Project Setup
```bash
# Clone or create project directory
mkdir test_api && cd test_api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Server
```bash
# Method 1: Using the automated script (recommended)
chmod +x run_server.sh
./run_server.sh

# Method 2: Manual start
python test_api_server.py
```

### 3. Verify Installation
```bash
# Test health endpoint (ngrok domain)
curl https://learning-teal-prepared.ngrok-free.app/api/health

# Test authenticated endpoint (ngrok domain)
curl -H "Authorization: Bearer ft_test_api_2024" https://learning-teal-prepared.ngrok-free.app/api/organizations

# Or test locally
curl http://localhost:3001/api/health
```

## 📁 Project Structure
```
test_api/
├── 📄 test_api_server.py              # Main Flask application (1,256 lines)
├── 📋 requirements.txt                # Python dependencies
├── 🚀 run_server.sh                  # Automated server startup script
├── 📖 README.md                      # This documentation
├── 📊 comprehensive_postman_collection.json  # Complete Postman collection
├── 🧪 tests/                         # Test suite
│   ├── test_api.py                   # Unit tests
│   └── locustfile.py                 # Performance tests
├── 📝 logs/                          # Application logs
│   └── flask.log                     # Flask server logs
├── 🐍 venv/                          # Virtual environment
└── 🗂️ __pycache__/                   # Python cache files
```

## 📚 API Documentation

### 🌐 Interactive Documentation
- **Swagger UI**: `https://learning-teal-prepared.ngrok-free.app/api/docs`
- **OpenAPI Spec**: `https://learning-teal-prepared.ngrok-free.app/api/openapi.json`
- **Postman Collection**: Import `comprehensive_postman_collection.json` (pre-configured with ngrok domain)
- **Local Access**: `http://localhost:3001/api/docs` (when testing locally)

### 📖 Documentation Features
- **Complete OpenAPI 3.0 Specification** - Machine-readable API documentation
- **Interactive Swagger UI** - Test endpoints directly in browser
- **Postman Collection** - Pre-configured requests with examples
- **Request/Response Schemas** - Detailed data structure documentation
- **Authentication Examples** - Working authentication examples
- **Error Response Documentation** - Complete error handling guide

## 🔐 Authentication & Security

### 🎫 Bearer Token Authentication
All endpoints (except health, version, and docs) require Bearer token authentication:

```bash
# Required header format
Authorization: Bearer ft_test_api_2024
```

### 🛡️ Security Features
- **Static Bearer Token**: `ft_test_api_2024` (configurable)
- **Request Validation**: All inputs validated and sanitized
- **Rate Limiting**: Configurable per-endpoint limits
- **Error Handling**: Secure error messages without data leakage

### ⚡ Rate Limits
| Endpoint Category | Rate Limit |
|------------------|------------|
| Root Endpoint | 10/minute |
| Health/Version | 30/minute |
| CRUD Operations | 100/minute |
| Batch Operations | 20/minute |
| Search Operations | 50/minute |
| Statistics | 30/minute |

## 🔗 Endpoints Reference

### 🏥 System Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/` | ❌ | API information and endpoint list |
| `GET` | `/api/health` | ❌ | Health check with timestamp |
| `GET` | `/api/version` | ❌ | API version information |
| `GET` | `/api/docs` | ❌ | Interactive Swagger UI documentation |
| `GET` | `/api/openapi.json` | ❌ | OpenAPI 3.0 specification |

### 🏢 Organizations Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/organizations` | ✅ | List organizations (paginated, filterable) |
| `POST` | `/api/organizations` | ✅ | Create new organization |
| `GET` | `/api/organizations/{id}` | ✅ | Get organization by ID with users |
| `PUT` | `/api/organizations/{id}` | ✅ | Update organization |
| `DELETE` | `/api/organizations/{id}` | ✅ | Delete organization |

### 👥 Users Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/users` | ✅ | List users (paginated, filterable) |
| `POST` | `/api/users` | ✅ | Create new user |
| `GET` | `/api/users/{id}` | ✅ | Get user by ID with organization |
| `PUT` | `/api/users/{id}` | ✅ | Update user |
| `DELETE` | `/api/users/{id}` | ✅ | Delete user |

### 👤 Profiles Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/profiles` | ✅ | List profiles (paginated, filterable) |
| `POST` | `/api/profiles` | ✅ | Create new profile |
| `GET` | `/api/profiles/{id}` | ✅ | Get profile by ID |
| `PUT` | `/api/profiles/{id}` | ✅ | Update profile |
| `DELETE` | `/api/profiles/{id}` | ✅ | Delete profile |

### 📊 Batch Operations
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/batch/organizations` | ✅ | Batch create organizations (max 50) |
| `POST` | `/api/batch/users` | ✅ | Batch create users (max 50) |

### 🔍 Search & Analytics
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/search/advanced` | ✅ | Multi-entity search with filters |
| `GET` | `/api/stats` | ✅ | API statistics and analytics |

## ✅ Validation & Error Handling

### 🛡️ Comprehensive Validation

#### Organization Validation
- **Required Fields**: `name`, `type`
- **Field Constraints**:
  - `name`: 1-100 characters, non-empty string
  - `type`: Must be one of: `test`, `enterprise`, `startup`, `nonprofit`, `government`
  - `id`: Must follow `ORG###` format (e.g., `ORG001`, `ORG123`)
- **Duplicate Prevention**: ID uniqueness enforced

#### User Validation
- **Required Fields**: `name`, `email`
- **Field Constraints**:
  - `name`: 1-100 characters, non-empty string
  - `email`: Valid email format, unique across all users
  - `organization_id`: Must reference existing organization
  - `id`: Must follow `USER###` format
- **Duplicate Prevention**: ID and email uniqueness enforced

#### Profile Validation
- **Required Fields**: `name`
- **Field Constraints**:
  - `name`: 1-100 characters, non-empty string
  - `settings`: Valid JSON object
  - `preferences`: Valid JSON object
  - `id`: Must follow `PROF###` format
- **Duplicate Prevention**: ID uniqueness enforced

### 🚨 Error Response Format
```json
{
  "error": "Detailed error message explaining what went wrong"
}
```

### 📋 HTTP Status Codes
| Status Code | Description | Usage |
|-------------|-------------|-------|
| `200 OK` | Success | GET, PUT operations |
| `201 Created` | Resource created | POST operations |
| `204 No Content` | Success, no response body | DELETE operations |
| `400 Bad Request` | Validation error | Invalid input data |
| `401 Unauthorized` | Authentication required | Missing/invalid token |
| `404 Not Found` | Resource not found | Invalid resource ID |
| `409 Conflict` | Duplicate resource | ID/email already exists |
| `429 Too Many Requests` | Rate limit exceeded | Too many requests |

### 🔍 Validation Examples

#### ✅ Valid Organization Creation
```bash
curl -X POST https://learning-teal-prepared.ngrok-free.app/api/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ft_test_api_2024" \
  -d '{
    "name": "Acme Corporation",
    "type": "enterprise",
    "id": "ORG500"
  }'
```

#### ❌ Invalid Organization Creation
```bash
curl -X POST https://learning-teal-prepared.ngrok-free.app/api/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ft_test_api_2024" \
  -d '{
    "name": "",
    "type": "invalid_type"
  }'

# Response: 400 Bad Request
{
  "error": "Field 'name' is required and cannot be empty"
}
```

## 🚀 Advanced Features

### 📄 Pagination
All list endpoints support pagination:
```bash
# Pagination parameters
GET /api/organizations?page=2&per_page=20

# Response format
{
  "items": [...],
  "total": 150,
  "page": 2,
  "per_page": 20,
  "total_pages": 8
}
```

### 🔍 Filtering
Filter on any field using query parameters:
```bash
# Single filter
GET /api/organizations?type=enterprise

# Multiple filters
GET /api/users?name=John&organization_id=ORG001

# Nested field filtering (if supported)
GET /api/users?metadata.version=1.0.0
```

### ⚡ Caching
Intelligent caching system:
- **GET requests**: Cached for 60 seconds
- **Cache invalidation**: Automatic on data modifications
- **Cache keys**: Based on endpoint + query parameters
- **Performance**: Significant response time improvement

### 🔄 Batch Operations
Bulk operations for efficiency:
```bash
# Batch create organizations
curl -X POST https://learning-teal-prepared.ngrok-free.app/api/batch/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ft_test_api_2024" \
  -d '{
    "operations": [
      {
        "action": "create",
        "data": {
          "name": "Company 1",
          "type": "startup"
        }
      },
      {
        "action": "create", 
        "data": {
          "name": "Company 2",
          "type": "enterprise",
          "id": "ORG600"
        }
      }
    ]
  }'

# Response format
{
  "results": [
    {
      "status": "success",
      "data": { ... }
    },
    {
      "status": "error",
      "error": "Operation 2: Organization with ID 'ORG600' already exists"
    }
  ]
}
```

### 🔍 Advanced Search
Multi-entity search with filters:
```bash
# Search all entities
GET /api/search/advanced?q=test&type=all&page=1&per_page=10

# Search specific entity type
GET /api/search/advanced?type=organizations&filters={"type":"enterprise"}

# Response includes entity type
{
  "items": [
    {
      "id": "ORG001",
      "name": "Test Corp",
      "type": "organization",
      ...
    }
  ],
  ...
}
```

### 📊 Statistics & Analytics
Real-time API statistics:
```bash
GET /api/stats

# Response
{
  "organizations": {
    "total": 25,
    "by_type": {
      "enterprise": 10,
      "startup": 8,
      "test": 7
    }
  },
  "users": {
    "total": 150,
    "by_organization": {
      "ORG001": 15,
      "ORG002": 12,
      ...
    }
  },
  "profiles": {
    "total": 150
  }
}
```

## 🧪 Testing

### 🔬 Test Suite
```bash
# Run unit tests
cd tests
python -m pytest test_api.py -v

# Run performance tests
pip install locust
locust -f locustfile.py --host=http://localhost:3000
```

### 📊 Test Coverage
- **Authentication tests** - Token validation and security
- **CRUD operations** - All endpoints tested
- **Validation tests** - Input validation and error handling
- **Rate limiting tests** - Rate limit enforcement
- **Performance tests** - Load testing with Locust

### 🧪 Manual Testing
```bash
# Test health check
curl https://learning-teal-prepared.ngrok-free.app/api/health

# Test authentication
curl -H "Authorization: Bearer ft_test_api_2024" \
  https://learning-teal-prepared.ngrok-free.app/api/organizations

# Test validation
curl -X POST https://learning-teal-prepared.ngrok-free.app/api/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ft_test_api_2024" \
  -d '{"name":"","type":"invalid"}'

# Test pagination
curl -H "Authorization: Bearer ft_test_api_2024" \
  "https://learning-teal-prepared.ngrok-free.app/api/organizations?page=1&per_page=5"
```

## 🚀 Deployment

### 🐳 Production Deployment
```bash
# Using Gunicorn (recommended)
gunicorn --bind 0.0.0.0:3000 --workers 4 test_api_server:app

# With environment variables
export BEARER_TOKEN=your_secure_token_here
export FLASK_ENV=production
gunicorn --bind 0.0.0.0:3000 test_api_server:app
```

### 🌐 Public Exposure with ngrok
```bash
# Install and configure ngrok
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Start tunnel
ngrok http --domain=your-domain.ngrok-free.app 3000
```

### ⚙️ Configuration
Environment variables:
- `BEARER_TOKEN` - API authentication token
- `FLASK_ENV` - Environment (development/production)
- `PORT` - Server port (default: 3000)

## 🔧 Troubleshooting

### 🚨 Common Issues

#### 1. **Server Won't Start**
```bash
# Check port availability
lsof -i :3000

# Kill existing processes
pkill -f "python.*test_api_server"

# Restart server
python test_api_server.py
```

#### 2. **Authentication Errors**
```bash
# Verify token format (ngrok domain)
curl -H "Authorization: Bearer ft_test_api_2024" \
  https://learning-teal-prepared.ngrok-free.app/api/health

# Or test locally
curl -H "Authorization: Bearer ft_test_api_2024" \
  http://localhost:3001/api/health

# Check for typos in token
echo "ft_test_api_2024" | wc -c  # Should be 17 characters
```

#### 3. **Validation Errors**
```bash
# Check required fields
curl -X POST https://learning-teal-prepared.ngrok-free.app/api/organizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ft_test_api_2024" \
  -d '{"name":"Test Org","type":"enterprise"}'  # Valid

# Check field formats
curl -X POST https://learning-teal-prepared.ngrok-free.app/api/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ft_test_api_2024" \
  -d '{"name":"John Doe","email":"john@example.com"}'  # Valid
```

#### 4. **Rate Limiting**
```bash
# Check rate limit headers
curl -I -H "Authorization: Bearer ft_test_api_2024" \
  https://learning-teal-prepared.ngrok-free.app/api/organizations

# Wait for rate limit reset or implement backoff
```

#### 5. **Dependencies Issues**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

### 📞 Support
For issues not covered in this guide:
1. Check the server logs: `tail -f logs/flask.log`
2. Verify API documentation: `https://learning-teal-prepared.ngrok-free.app/api/docs`
3. Test with Postman collection: Import `comprehensive_postman_collection.json` (pre-configured with ngrok)
4. Run the test suite: `python -m pytest tests/test_api.py`
5. Check ngrok status: `curl http://localhost:4040/api/tunnels`

---

## 📝 API Summary

This **Test API** provides a complete, production-ready RESTful API with:
- ✅ **Complete CRUD operations** for organizations, users, and profiles
- ✅ **Enterprise-grade validation** with detailed error messages
- ✅ **Bearer token authentication** with rate limiting
- ✅ **OpenAPI 3.0 documentation** with interactive Swagger UI
- ✅ **Batch operations** for bulk data processing
- ✅ **Advanced search** across multiple entity types
- ✅ **Intelligent caching** for improved performance
- ✅ **Comprehensive test suite** with unit and performance tests
- ✅ **Production deployment** ready with Gunicorn

**🚀 Ready for production use with enterprise-grade features and comprehensive documentation!** 