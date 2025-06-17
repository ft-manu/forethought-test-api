from flask import Flask, jsonify, request, abort, send_from_directory
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from functools import wraps
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
from collections import defaultdict
from flask import Blueprint


app = Flask(__name__)
Compress(app)  # Enable compression

# Rate Limiting Configuration
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Cache Configuration
cache = Cache(app, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
})

# Security
BEARER_TOKEN = "ft_test_api_2024"

# Validation Functions
def validate_json_payload(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate that the request has valid JSON payload"""
    if not data:
        return False, "Request body must contain valid JSON"
    return True, None

def validate_organization_data(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate organization data with comprehensive checks"""
    # Check required fields for creation
    if not is_update:
        if not data.get('name'):
            return False, "Field 'name' is required and cannot be empty"
        if not data.get('type'):
            return False, "Field 'type' is required and cannot be empty"
    
    # Validate name if provided
    if 'name' in data:
        name = data['name']
        if not isinstance(name, str) or len(name.strip()) == 0:
            return False, "Field 'name' must be a non-empty string"
        if len(name) > 100:
            return False, "Field 'name' must be 100 characters or less"
    
    # Validate type if provided
    if 'type' in data:
        org_type = data['type']
        valid_types = ['test', 'enterprise', 'startup', 'nonprofit', 'government']
        if not isinstance(org_type, str) or org_type not in valid_types:
            return False, f"Field 'type' must be one of: {', '.join(valid_types)}"
    
    # Validate ID format if provided
    if 'id' in data:
        org_id = data['id']
        if not isinstance(org_id, str) or not re.match(r'^ORG\d{3,}$', org_id):
            return False, "Field 'id' must follow format 'ORG###' (e.g., 'ORG001', 'ORG123')"
    
    return True, None

def validate_user_data(data: Dict[str, Any], is_update: bool = False, exclude_user_id: str = None) -> Tuple[bool, Optional[str]]:
    """Validate user data with comprehensive checks"""
    # Check required fields for creation
    if not is_update:
        if not data.get('name'):
            return False, "Field 'name' is required and cannot be empty"
        if not data.get('email'):
            return False, "Field 'email' is required and cannot be empty"
    
    # Validate name if provided
    if 'name' in data:
        name = data['name']
        if not isinstance(name, str) or len(name.strip()) == 0:
            return False, "Field 'name' must be a non-empty string"
        if len(name) > 100:
            return False, "Field 'name' must be 100 characters or less"
    
    # Validate email if provided
    if 'email' in data:
        email = data['email']
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not isinstance(email, str) or not re.match(email_pattern, email):
            return False, "Field 'email' must be a valid email address"
        
        # Check for duplicate email (excluding current user in updates)
        existing_user = next((user for user in SAMPLE_USERS if user["email"] == email and user["id"] != exclude_user_id), None)
        if existing_user:
            return False, f"Email '{email}' is already in use by another user"
    
    # Validate organization_id if provided
    if 'organization_id' in data:
        org_id = data['organization_id']
        if org_id:  # Allow None/empty for optional field
            existing_org = next((org for org in SAMPLE_ORGANIZATIONS if org["id"] == org_id), None)
            if not existing_org:
                return False, f"Organization with ID '{org_id}' does not exist"
    
    # Validate ID format if provided
    if 'id' in data:
        user_id = data['id']
        if not isinstance(user_id, str) or not re.match(r'^USER\d{3,}', user_id):
            return False, "Field 'id' must follow format 'USER###' (e.g., 'USER001', 'USER123')"
    
    return True, None

def validate_profile_data(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate profile data with comprehensive checks"""
    # Check required fields for creation
    if not is_update:
        if not data.get('name'):
            return False, "Field 'name' is required and cannot be empty"
    
    # Validate name if provided
    if 'name' in data:
        name = data['name']
        if not isinstance(name, str) or len(name.strip()) == 0:
            return False, "Field 'name' must be a non-empty string"
        if len(name) > 100:
            return False, "Field 'name' must be 100 characters or less"
    
    # Validate settings if provided
    if 'settings' in data:
        settings = data['settings']
        if not isinstance(settings, dict):
            return False, "Field 'settings' must be a valid JSON object"
    
    # Validate preferences if provided
    if 'preferences' in data:
        preferences = data['preferences']
        if not isinstance(preferences, dict):
            return False, "Field 'preferences' must be a valid JSON object"
    
    # Validate ID format if provided
    if 'id' in data:
        profile_id = data['id']
        if not isinstance(profile_id, str) or not re.match(r'^PROF\d{3,}', profile_id):
            return False, "Field 'id' must follow format 'PROF###' (e.g., 'PROF001', 'PROF123')"
    
    return True, None

def check_duplicate_id(entity_type: str, entity_id: str, exclude_id: str = None) -> Tuple[bool, Optional[str]]:
    """Check for duplicate IDs across all entity types"""
    collections = {
        'organization': SAMPLE_ORGANIZATIONS,
        'user': SAMPLE_USERS,
        'profile': SAMPLE_PROFILES
    }
    
    if entity_type not in collections:
        return False, f"Invalid entity type: {entity_type}"
    
    collection = collections[entity_type]
    existing_entity = next((item for item in collection if item["id"] == entity_id and item["id"] != exclude_id), None)
    
    if existing_entity:
        return False, f"{entity_type.capitalize()} with ID '{entity_id}' already exists"
    
    return True, None

def validate_batch_operations(operations: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """Validate batch operations structure"""
    if not isinstance(operations, list):
        return False, "Field 'operations' must be an array"
    
    if len(operations) == 0:
        return False, "Field 'operations' cannot be empty"
    
    if len(operations) > 50:
        return False, "Batch operations limited to 50 items per request"
    
    for i, op in enumerate(operations):
        if not isinstance(op, dict):
            return False, f"Operation {i+1}: must be a valid object"
        
        if 'action' not in op:
            return False, f"Operation {i+1}: field 'action' is required"
        
        if op['action'] not in ['create', 'update', 'delete']:
            return False, f"Operation {i+1}: field 'action' must be one of: create, update, delete"
        
        if 'data' not in op:
            return False, f"Operation {i+1}: field 'data' is required"
        
        if not isinstance(op['data'], dict):
            return False, f"Operation {i+1}: field 'data' must be a valid object"
    
    return True, None

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        if token != BEARER_TOKEN:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    return decorated

# Helper function to create nested profile with 10 levels
def create_nested_profile(level: int = 10) -> Dict[str, Any]:
    if level == 1:
        return {
            "data": f"Level {level} data",
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "version": "1.0.0"
            }
        }
    return {
        f"level{level}": create_nested_profile(level - 1),
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "version": "1.0.0"
        }
    }

# Helper function to create sample data
def create_sample_data():
    organizations = []
    users = []
    profiles = []
    
    # Create 10 organizations
    for i in range(1, 11):
        org_id = f"ORG{i:03d}"
        organizations.append({
            "id": org_id,
            "name": f"Test Organization {i}",
            "type": "test",
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "version": "1.0.0"
            }
        })
        
        # Create 10 users per organization
        for j in range(1, 11):
            user_id = f"USER{i:03d}_{j:03d}"
            profile = create_nested_profile()
            profile_id = f"PROF{i:03d}_{j:03d}"
            profile["id"] = profile_id
            profiles.append(profile)
            
            users.append({
                "id": user_id,
                "name": f"Test User {i}-{j}",
                "email": f"test{i}_{j}@example.com",
                "organization_id": org_id,
                "profile_id": profile_id,
                "metadata": {
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "version": "1.0.0"
                }
            })
    
    return organizations, users, profiles

# Create sample data
SAMPLE_ORGANIZATIONS, SAMPLE_USERS, SAMPLE_PROFILES = create_sample_data()

# Helper functions for pagination and filtering
def paginate_data(data: List[Any], page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    return {
        "items": data[start_idx:end_idx],
        "total": len(data),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(data) + per_page - 1) // per_page
    }

# Enhanced filter function with nested field support and text search
def filter_data(data: List[Any], filters: Dict[str, Any]) -> List[Any]:
    """
    Filter data based on provided filters dictionary.
    Supports nested field filtering using dot notation (e.g., "metadata.version").
    """
    filtered = data
    for key, value in filters.items():
        if '.' in key:
            # Handle nested field filtering
            filtered = [item for item in filtered if _get_nested_value(item, key, value)]
        else:
            # Handle top-level field filtering
            filtered = [item for item in filtered if str(_get_field_value(item, key)).lower().find(str(value).lower()) != -1]
    return filtered

def _get_nested_value(item: Dict[str, Any], key_path: str, search_value: str) -> bool:
    """
    Get value from nested dictionary using dot notation.
    Returns True if the search_value is found in the nested field.
    """
    keys = key_path.split('.')
    current = item
    
    try:
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        
        return str(current).lower().find(str(search_value).lower()) != -1
    except:
        return False

def _get_field_value(item: Dict[str, Any], key: str) -> str:
    """
    Get field value with fallback to empty string.
    """
    return str(item.get(key, ''))

def search_in_text(data: List[Any], query: str) -> List[Any]:
    """
    Perform text search across all string fields in the data.
    Searches in: name, email, id, and nested string values.
    """
    if not query:
        return data
    
    query_lower = query.lower()
    results = []
    
    for item in data:
        if _item_matches_query(item, query_lower):
            results.append(item)
    
    return results

def _item_matches_query(item: Any, query_lower: str) -> bool:
    """
    Check if an item matches the search query by searching all string fields.
    """
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and query_lower in value.lower():
                return True
            elif isinstance(value, (dict, list)):
                if _item_matches_query(value, query_lower):
                    return True
    elif isinstance(item, list):
        for sub_item in item:
            if _item_matches_query(sub_item, query_lower):
                return True
    elif isinstance(item, str):
        return query_lower in item.lower()
    
    return False

# Root endpoint
@app.route('/')
@limiter.limit("10 per minute")  # Stricter limit for root endpoint
@cache.cached(timeout=60)  # Cache for 1 minute
def root():
    return jsonify({
        "api": "Test API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "organizations": "/api/organizations",
            "users": "/api/users",
            "organization": "/api/organizations/{id}",
            "user": "/api/user/{id}",
            "search": "/api/search",
            "health": "/api/health",
            "version": "/api/version",
            "profiles": "/api/profiles",
            "stats": "/api/stats",
            "batch": "/api/batch"
        }
    })

# Health check endpoint
@app.route('/api/health')
@limiter.limit("30 per minute")
@cache.cached(timeout=30)  # Cache for 30 seconds
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

# Version endpoint
@app.route('/api/version')
@limiter.limit("30 per minute")
@cache.cached(timeout=300)  # Cache for 5 minutes
def version():
    return jsonify({
        "version": "1.0.0",
        "build": "2024.1.0",
        "environment": "development"
    })

# Organizations endpoints
@app.route('/api/organizations', methods=['GET', 'POST'])
@require_token
@limiter.limit("100 per minute")
def handle_organizations():
    if request.method == 'POST':
        # Clear all cached GET responses when data is modified
        cache.clear()
        
        # Get and validate JSON payload
        try:
            data = request.get_json()
        except Exception:
            return jsonify({"error": "Invalid JSON in request body"}), 400
        
        # Validate JSON payload
        is_valid, error_msg = validate_json_payload(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Validate organization data
        is_valid, error_msg = validate_organization_data(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Handle ID assignment and duplicate checking
        provided_id = data.get('id')
        if provided_id:
            # Check for duplicate ID
            is_valid, error_msg = check_duplicate_id('organization', provided_id)
            if not is_valid:
                return jsonify({"error": error_msg}), 409
            org_id = provided_id
        else:
            # Auto-generate ID
            org_id = f"ORG{len(SAMPLE_ORGANIZATIONS) + 1:03d}"
            # Ensure auto-generated ID doesn't conflict
            while any(org["id"] == org_id for org in SAMPLE_ORGANIZATIONS):
                org_id = f"ORG{len(SAMPLE_ORGANIZATIONS) + 2:03d}"
        
        new_org = {
            "id": org_id,
            "name": data['name'],
            "type": data['type'],
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        }
        SAMPLE_ORGANIZATIONS.append(new_org)
        return jsonify(new_org), 201
    
    # GET request - Create cache key based on all query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    filters = {k: v for k, v in request.args.items() if k not in ['page', 'per_page']}
    
    # Create a consistent cache key
    cache_key = f"organizations_page_{page}_per_page_{per_page}_filters_{sorted(filters.items())}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
    # Generate response
    filtered_orgs = filter_data(SAMPLE_ORGANIZATIONS, filters)
    result = paginate_data(filtered_orgs, page, per_page)
    
    # Cache the result for 60 seconds
    cache.set(cache_key, result, timeout=60)
    
    return jsonify(result)

@app.route('/api/organizations/<org_id>', methods=['GET', 'PUT', 'DELETE'])
@require_token
@limiter.limit("100 per minute")
@cache.cached(timeout=60, query_string=True)  # Cache GET requests
def handle_organization(org_id):
    org = next((org for org in SAMPLE_ORGANIZATIONS if org["id"] == org_id), None)
    if not org:
        return jsonify({"error": "Organization not found"}), 404
    
    if request.method in ['PUT', 'DELETE']:
        cache.clear()  # Clear all cache on modification
    
    if request.method == 'DELETE':
        SAMPLE_ORGANIZATIONS.remove(org)
        return '', 204
    
    if request.method == 'PUT':
        data = request.get_json()
        org.update({
            "name": data.get('name', org['name']),
            "type": data.get('type', org['type']),
            "metadata": {
                **org['metadata'],
                "updated_at": datetime.utcnow().isoformat()
            }
        })
        return jsonify(org)
    
    # GET request
    org_users = [user for user in SAMPLE_USERS if user["organization_id"] == org_id]
    org["users"] = org_users
    org["total_users"] = len(org_users)
    return jsonify(org)

# Users endpoints
@app.route('/api/users', methods=['GET', 'POST'])
@require_token
@limiter.limit("100 per minute")
def handle_users():
    if request.method == 'POST':
        # Clear all cached GET responses when data is modified
        cache.clear()
        
        # Get and validate JSON payload
        try:
            data = request.get_json()
        except Exception:
            return jsonify({"error": "Invalid JSON in request body"}), 400
        
        # Validate JSON payload
        is_valid, error_msg = validate_json_payload(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Validate user data
        is_valid, error_msg = validate_user_data(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Handle ID assignment and duplicate checking
        provided_id = data.get('id')
        if provided_id:
            # Check for duplicate ID
            is_valid, error_msg = check_duplicate_id('user', provided_id)
            if not is_valid:
                return jsonify({"error": error_msg}), 409
            user_id = provided_id
        else:
            # Auto-generate ID
            user_id = f"USER{len(SAMPLE_USERS) + 1:03d}"
            # Ensure auto-generated ID doesn't conflict
            while any(user["id"] == user_id for user in SAMPLE_USERS):
                user_id = f"USER{len(SAMPLE_USERS) + 2:03d}"
        
        new_user = {
            "id": user_id,
            "name": data['name'],
            "email": data['email'],
            "organization_id": data.get('organization_id'),
            "profile_id": f"PROF{len(SAMPLE_PROFILES) + 1:03d}",
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        }
        SAMPLE_USERS.append(new_user)
        return jsonify(new_user), 201
    
    # GET request - Create cache key based on all query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    filters = {k: v for k, v in request.args.items() if k not in ['page', 'per_page']}
    
    # Create a consistent cache key
    cache_key = f"users_page_{page}_per_page_{per_page}_filters_{sorted(filters.items())}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
    # Generate response
    filtered_users = filter_data(SAMPLE_USERS, filters)
    result = paginate_data(filtered_users, page, per_page)
    
    # Cache the result for 60 seconds
    cache.set(cache_key, result, timeout=60)
    
    return jsonify(result)

@app.route('/api/users/<user_id>', methods=['GET', 'PUT', 'DELETE'])
@require_token
@limiter.limit("100 per minute")
def handle_user(user_id):
    user = next((user for user in SAMPLE_USERS if user["id"] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if request.method in ['PUT', 'DELETE']:
        cache.clear()  # Clear all cache on modification
    
    if request.method == 'DELETE':
        SAMPLE_USERS.remove(user)
        return '', 204
    
    if request.method == 'PUT':
        data = request.get_json()
        user.update({
            "name": data.get('name', user['name']),
            "email": data.get('email', user['email']),
            "organization_id": data.get('organization_id', user['organization_id']),
            "metadata": {
                **user['metadata'],
                "updated_at": datetime.utcnow().isoformat()
            }
        })
        return jsonify(user)
    
    # GET request
    org = next((org for org in SAMPLE_ORGANIZATIONS if org["id"] == user["organization_id"]), None)
    if org:
        user["organization"] = org
    return jsonify(user)

# Profile endpoints
@app.route('/api/profiles', methods=['GET', 'POST'])
@require_token
@limiter.limit("100 per minute")
def handle_profiles():
    if request.method == 'POST':
        # Clear all cached GET responses when data is modified
        cache.clear()
        
        # Get and validate JSON payload
        try:
            data = request.get_json()
        except Exception:
            return jsonify({"error": "Invalid JSON in request body"}), 400
        
        # Validate JSON payload
        is_valid, error_msg = validate_json_payload(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Validate profile data
        is_valid, error_msg = validate_profile_data(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400
        
        # Handle ID assignment and duplicate checking
        provided_id = data.get('id')
        if provided_id:
            # Check for duplicate ID
            is_valid, error_msg = check_duplicate_id('profile', provided_id)
            if not is_valid:
                return jsonify({"error": error_msg}), 409
            profile_id = provided_id
        else:
            # Auto-generate ID
            profile_id = f"PROF{len(SAMPLE_PROFILES) + 1:03d}"
            # Ensure auto-generated ID doesn't conflict
            while any(profile["id"] == profile_id for profile in SAMPLE_PROFILES):
                profile_id = f"PROF{len(SAMPLE_PROFILES) + 2:03d}"
        
        new_profile = {
            "id": profile_id,
            "name": data['name'],
            "settings": data.get('settings', {}),
            "preferences": data.get('preferences', {}),
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        }
        SAMPLE_PROFILES.append(new_profile)
        return jsonify(new_profile), 201
    
    # GET request - Create cache key based on all query parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    filters = {k: v for k, v in request.args.items() if k not in ['page', 'per_page']}
    
    # Create a consistent cache key
    cache_key = f"profiles_page_{page}_per_page_{per_page}_filters_{sorted(filters.items())}"
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result:
        return jsonify(cached_result)
    
    # Generate response
    filtered_profiles = filter_data(SAMPLE_PROFILES, filters)
    result = paginate_data(filtered_profiles, page, per_page)
    
    # Cache the result for 60 seconds
    cache.set(cache_key, result, timeout=60)
    
    return jsonify(result)

@app.route('/api/profiles/<profile_id>', methods=['GET', 'PUT', 'DELETE'])
@require_token
@limiter.limit("100 per minute")
def handle_profile(profile_id):
    profile = next((p for p in SAMPLE_PROFILES if p["id"] == profile_id), None)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    if request.method in ['PUT', 'DELETE']:
        cache.clear()  # Clear all cache on modification
    
    if request.method == 'DELETE':
        SAMPLE_PROFILES.remove(profile)
        return '', 204
    
    if request.method == 'PUT':
        data = request.get_json()
        profile.update({
            "name": data.get('name', profile.get('name')),
            "settings": data.get('settings', profile.get('settings', {})),
            "preferences": data.get('preferences', profile.get('preferences', {})),
            "metadata": {
                **profile.get('metadata', {}),
                "updated_at": datetime.utcnow().isoformat()
            }
        })
        return jsonify(profile)
    
    return jsonify(profile)

# Statistics endpoints
@app.route('/api/stats')
@require_token
@limiter.limit("30 per minute")
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_stats():
    stats = {
        "organizations": {
            "total": len(SAMPLE_ORGANIZATIONS),
            "by_type": defaultdict(int)
        },
        "users": {
            "total": len(SAMPLE_USERS),
            "by_organization": defaultdict(int)
        },
        "profiles": {
            "total": len(SAMPLE_PROFILES)
        }
    }
    
    for org in SAMPLE_ORGANIZATIONS:
        stats["organizations"]["by_type"][org["type"]] += 1
    
    for user in SAMPLE_USERS:
        stats["users"]["by_organization"][user["organization_id"]] += 1
    
    return jsonify(stats)

# Batch operations
@app.route('/api/batch/organizations', methods=['POST'])
@require_token
@limiter.limit("20 per minute")  # Stricter limit for batch operations
def batch_organizations():
    # Get and validate JSON payload
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON in request body"}), 400
    
    # Validate JSON payload
    is_valid, error_msg = validate_json_payload(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    # Validate batch operations structure
    operations = data.get('operations', [])
    is_valid, error_msg = validate_batch_operations(operations)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    results = []
    
    for i, op in enumerate(operations):
        if op['action'] == 'create':
            try:
                # Validate organization data
                is_valid, error_msg = validate_organization_data(op['data'])
                if not is_valid:
                    results.append({"status": "error", "error": f"Operation {i+1}: {error_msg}"})
                    continue
                
                # Handle ID assignment and duplicate checking
                provided_id = op['data'].get('id')
                if provided_id:
                    # Check for duplicate ID
                    is_valid, error_msg = check_duplicate_id('organization', provided_id)
                    if not is_valid:
                        results.append({"status": "error", "error": f"Operation {i+1}: {error_msg}"})
                        continue
                    org_id = provided_id
                else:
                    # Auto-generate ID
                    org_id = f"ORG{len(SAMPLE_ORGANIZATIONS) + 1:03d}"
                    # Ensure auto-generated ID doesn't conflict
                    while any(org["id"] == org_id for org in SAMPLE_ORGANIZATIONS):
                        org_id = f"ORG{len(SAMPLE_ORGANIZATIONS) + 2:03d}"
                
                new_org = {
                    "id": org_id,
                    "name": op['data']['name'],
                    "type": op['data']['type'],
                    "metadata": {
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "version": "1.0.0"
                    }
                }
                SAMPLE_ORGANIZATIONS.append(new_org)
                results.append({"status": "success", "data": new_org})
            except Exception as e:
                results.append({"status": "error", "error": f"Operation {i+1}: {str(e)}"})
    
    # Clear relevant caches
    cache.clear()
    
    return jsonify({"results": results})

@app.route('/api/batch/users', methods=['POST'])
@require_token
@limiter.limit("20 per minute")  # Stricter limit for batch operations
def batch_users():
    # Get and validate JSON payload
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON in request body"}), 400
    
    # Validate JSON payload
    is_valid, error_msg = validate_json_payload(data)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    # Validate batch operations structure
    operations = data.get('operations', [])
    is_valid, error_msg = validate_batch_operations(operations)
    if not is_valid:
        return jsonify({"error": error_msg}), 400
    
    results = []
    
    for i, op in enumerate(operations):
        if op['action'] == 'create':
            try:
                # Validate user data
                is_valid, error_msg = validate_user_data(op['data'])
                if not is_valid:
                    results.append({"status": "error", "error": f"Operation {i+1}: {error_msg}"})
                    continue
                
                # Handle ID assignment and duplicate checking
                provided_id = op['data'].get('id')
                if provided_id:
                    # Check for duplicate ID
                    is_valid, error_msg = check_duplicate_id('user', provided_id)
                    if not is_valid:
                        results.append({"status": "error", "error": f"Operation {i+1}: {error_msg}"})
                        continue
                    user_id = provided_id
                else:
                    # Auto-generate ID
                    user_id = f"USER{len(SAMPLE_USERS) + 1:03d}"
                    # Ensure auto-generated ID doesn't conflict
                    while any(user["id"] == user_id for user in SAMPLE_USERS):
                        user_id = f"USER{len(SAMPLE_USERS) + 2:03d}"
                
                new_user = {
                    "id": user_id,
                    "name": op['data']['name'],
                    "email": op['data']['email'],
                    "organization_id": op['data'].get('organization_id'),
                    "profile_id": f"PROF{len(SAMPLE_PROFILES) + 1:03d}",
                    "metadata": {
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "version": "1.0.0"
                    }
                }
                SAMPLE_USERS.append(new_user)
                results.append({"status": "success", "data": new_user})
            except Exception as e:
                results.append({"status": "error", "error": f"Operation {i+1}: {str(e)}"})
    
    # Clear relevant caches
    cache.clear()
    
    return jsonify({"results": results})

# Advanced search endpoint
@app.route('/api/search/advanced')
@require_token
@limiter.limit("50 per minute")  # Stricter limit for search
@cache.cached(timeout=60, query_string=True)  # Cache search results
def advanced_search():
    query = request.args.get('q', '')
    entity_type = request.args.get('type', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    filters = request.args.get('filters', '{}')
    
    try:
        filters = json.loads(filters)
    except:
        filters = {}
    
    results = []
    
    # Apply search and filtering to organizations
    if entity_type in ['all', 'organizations']:
        org_data = SAMPLE_ORGANIZATIONS
        
        # Apply text search first if query is provided
        if query:
            org_data = search_in_text(org_data, query)
        
        # Apply filters
        org_results = filter_data(org_data, filters)
        results.extend([{**org, 'type': 'organization'} for org in org_results])
    
    # Apply search and filtering to users
    if entity_type in ['all', 'users']:
        user_data = SAMPLE_USERS
        
        # Apply text search first if query is provided
        if query:
            user_data = search_in_text(user_data, query)
        
        # Apply filters
        user_results = filter_data(user_data, filters)
        results.extend([{**user, 'type': 'user'} for user in user_results])
    
    # Apply search and filtering to profiles
    if entity_type in ['all', 'profiles']:
        profile_data = SAMPLE_PROFILES
        
        # Apply text search first if query is provided
        if query:
            profile_data = search_in_text(profile_data, query)
        
        # Apply filters
        profile_results = filter_data(profile_data, filters)
        results.extend([{**profile, 'type': 'profile'} for profile in profile_results])
    
    return jsonify(paginate_data(results, page, per_page))

# --- OpenAPI/Swagger Documentation ---
openapi_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "1.0.0",
        "description": "RESTful API for organizations, users, and profiles. All endpoints require Bearer token authentication."
    },
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        },
        "schemas": {
            "Organization": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "metadata": {"type": "object"},
                    "users": {"type": "array", "items": {"type": "object"}},
                    "total_users": {"type": "integer"}
                }
            },
            "OrganizationInput": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["name", "type", "metadata"]
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "organization_id": {"type": "string"},
                    "profile_id": {"type": "string"},
                    "metadata": {"type": "object"}
                }
            },
            "UserInput": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "organization_id": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["name", "email", "organization_id", "metadata"]
            },
            "Profile": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "metadata": {"type": "object"}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"}
                }
            }
        }
    },
    "security": [{"bearerAuth": []}],
    "paths": {
        "/api/health": {
            "get": {
                "summary": "Health check endpoint",
                "description": "Returns the health status of the API",
                "security": [],
                "responses": {
                    "200": {
                        "description": "API is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string", "example": "healthy"},
                                        "timestamp": {"type": "string", "format": "date-time"},
                                        "version": {"type": "string", "example": "1.0.0"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/version": {
            "get": {
                "summary": "Get API version information",
                "description": "Returns version and build information",
                "security": [],
                "responses": {
                    "200": {
                        "description": "Version information",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "version": {"type": "string", "example": "1.0.0"},
                                        "build": {"type": "string", "example": "2024.1.0"},
                                        "environment": {"type": "string", "example": "development"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/organizations": {
            "get": {
                "summary": "List organizations",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "name", "in": "query", "schema": {"type": "string"}},
                    {"name": "type", "in": "query", "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "A paginated list of organizations",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create organization",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/OrganizationInput"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Organization created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Organization"}
                            }
                        }
                    }
                }
            }
        },
        "/api/organizations/{org_id}": {
            "get": {
                "summary": "Get organization by ID",
                "parameters": [{"name": "org_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "200": {
                        "description": "Organization details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Organization"}
                            }
                        }
                    },
                    "404": {"description": "Not found"}
                }
            },
            "put": {
                "summary": "Update organization",
                "parameters": [{"name": "org_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/OrganizationInput"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Organization updated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Organization"}
                            }
                        }
                    },
                    "404": {"description": "Not found"}
                }
            },
            "delete": {
                "summary": "Delete organization",
                "parameters": [{"name": "org_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "204": {"description": "Deleted"},
                    "404": {"description": "Not found"}
                }
            }
        },
        "/api/users": {
            "get": {
                "summary": "List users",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "name", "in": "query", "schema": {"type": "string"}},
                    {"name": "email", "in": "query", "schema": {"type": "string"}},
                    {"name": "organization_id", "in": "query", "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "A paginated list of users",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/UserInput"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "User created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    }
                }
            }
        },
        "/api/users/{user_id}": {
            "get": {
                "summary": "Get user by ID",
                "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "200": {
                        "description": "User details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    },
                    "404": {"description": "Not found"}
                }
            },
            "put": {
                "summary": "Update user",
                "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/UserInput"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "User updated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    },
                    "404": {"description": "Not found"}
                }
            },
            "delete": {
                "summary": "Delete user",
                "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "204": {"description": "Deleted"},
                    "404": {"description": "Not found"}
                }
            }
        },
        "/api/profiles": {
            "get": {
                "summary": "List profiles",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "name", "in": "query", "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "A paginated list of profiles",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
        },
        "/api/profiles/{profile_id}": {
            "get": {
                "summary": "Get profile by ID",
                "parameters": [{"name": "profile_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {
                    "200": {
                        "description": "Profile details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Profile"}
                            }
                        }
                    },
                    "404": {"description": "Not found"}
                }
            },
            "put": {
                "summary": "Update profile",
                "parameters": [{"name": "profile_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Profile updated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Profile"}
                            }
                        }
                    },
                    "404": {"description": "Not found"}
                }
            }
        },
        "/api/stats": {
            "get": {
                "summary": "Get statistics",
                "responses": {
                    "200": {
                        "description": "Statistics object",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
        },
        "/api/search/advanced": {
            "get": {
                "summary": "Advanced search across organizations, users, and profiles",
                "description": "Perform text search and apply filters across multiple entity types. Supports nested field filtering using dot notation.",
                "parameters": [
                    {
                        "name": "q", 
                        "in": "query", 
                        "schema": {"type": "string"},
                        "description": "Text search query. Searches across all string fields including names, emails, and nested values.",
                        "example": "Test Organization"
                    },
                    {
                        "name": "type", 
                        "in": "query", 
                        "schema": {"type": "string", "enum": ["all", "organizations", "users", "profiles"]},
                        "description": "Entity type to search. Defaults to 'all'.",
                        "example": "organizations"
                    },
                    {
                        "name": "filters", 
                        "in": "query", 
                        "schema": {"type": "string"},
                        "description": "JSON string of filters to apply. Supports nested field filtering with dot notation (e.g., 'metadata.version').",
                        "example": "{\"name\":\"Organization 1\",\"metadata.version\":\"1.0.0\"}"
                    },
                    {
                        "name": "page", 
                        "in": "query", 
                        "schema": {"type": "integer", "minimum": 1},
                        "description": "Page number for pagination. Defaults to 1.",
                        "example": 1
                    },
                    {
                        "name": "per_page", 
                        "in": "query", 
                        "schema": {"type": "integer", "minimum": 1, "maximum": 100},
                        "description": "Number of items per page. Defaults to 10, maximum 100.",
                        "example": 10
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Paginated search results with metadata",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "items": {
                                            "type": "array",
                                            "description": "Array of matching entities with 'type' field added"
                                        },
                                        "total": {"type": "integer", "description": "Total number of matching items"},
                                        "page": {"type": "integer", "description": "Current page number"},
                                        "per_page": {"type": "integer", "description": "Items per page"},
                                        "total_pages": {"type": "integer", "description": "Total number of pages"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid filters JSON format",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    },
                    "401": {
                        "description": "Unauthorized - Invalid or missing bearer token",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        },
        "/api/batch/organizations": {
            "post": {
                "summary": "Batch operations for organizations",
                "description": "Perform multiple create, update, or delete operations on organizations in a single request",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "operations": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "action": {"type": "string", "enum": ["create", "update", "delete"]},
                                                "data": {"type": "object", "description": "Organization data (required for create/update)"},
                                                "id": {"type": "string", "description": "Organization ID (required for update/delete)"}
                                            },
                                            "required": ["action"]
                                        }
                                    }
                                },
                                "required": ["operations"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Batch operation results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "results": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "data": {"type": "object"},
                                                    "error": {"type": "string"}
                                                }
                                            }
                                        },
                                        "summary": {
                                            "type": "object",
                                            "properties": {
                                                "total": {"type": "integer"},
                                                "successful": {"type": "integer"},
                                                "failed": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request format",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        },
        "/api/batch/users": {
            "post": {
                "summary": "Batch operations for users",
                "description": "Perform multiple create, update, or delete operations on users in a single request",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "operations": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "action": {"type": "string", "enum": ["create", "update", "delete"]},
                                                "data": {"type": "object", "description": "User data (required for create/update)"},
                                                "id": {"type": "string", "description": "User ID (required for update/delete)"}
                                            },
                                            "required": ["action"]
                                        }
                                    }
                                },
                                "required": ["operations"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Batch operation results",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "results": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "data": {"type": "object"},
                                                    "error": {"type": "string"}
                                                }
                                            }
                                        },
                                        "summary": {
                                            "type": "object",
                                            "properties": {
                                                "total": {"type": "integer"},
                                                "successful": {"type": "integer"},
                                                "failed": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request format",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        }
    }
}

@app.route('/api/openapi.json')
def openapi_json():
    return jsonify(openapi_spec)

@app.route('/api/docs')
def swagger_ui():
    # Serve Swagger UI using the online CDN and point it to /api/openapi.json
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Test API Docs</title>
      <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist/swagger-ui.css" />
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
      <script>
        const ui = SwaggerUIBundle({
          url: '/api/openapi.json',
          dom_id: '#swagger-ui',
        });
      </script>
    </body>
    </html>
    '''
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000) 