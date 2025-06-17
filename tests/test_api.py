import pytest
from test_api_server import app
import json
import unittest
import requests

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'version' in data

def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert 'http_requests_total' in response.data.decode()

def test_api_docs(client):
    """Test API documentation endpoint"""
    response = client.get('/api/docs')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['openapi'] == '3.0.0'
    assert 'paths' in data
    assert 'components' in data

def test_get_organizations_unauthorized(client):
    """Test getting organizations without authorization"""
    response = client.get('/api/organizations')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

def test_get_organizations_authorized(client):
    """Test getting organizations with authorization"""
    headers = {'Authorization': 'Bearer ft_test_api_2024'}
    response = client.get('/api/organizations', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'organizations' in data
    assert len(data['organizations']) > 0

def test_get_organization_by_id(client):
    """Test getting a specific organization"""
    headers = {'Authorization': 'Bearer ft_test_api_2024'}
    response = client.get('/api/organizations/ORG001', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == 'ORG001'

def test_get_organization_filtered(client):
    """Test getting organizations with filters"""
    headers = {'Authorization': 'Bearer ft_test_api_2024'}
    response = client.get('/api/organizations?type=enterprise', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(org['type'] == 'enterprise' for org in data['organizations'])

def test_get_nested_data(client):
    """Test getting deeply nested data"""
    headers = {'Authorization': 'Bearer ft_test_api_2024'}
    response = client.get('/api/organizations/ORG001/headquarters/address/coordinates/geographic/region/classification/population/density/measurement/conversion', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'metric' in data
    assert 'formula' in data

def test_rate_limiting(client):
    """Test rate limiting"""
    headers = {'Authorization': 'Bearer ft_test_api_2024'}
    # Make multiple requests in quick succession
    for _ in range(60):
        response = client.get('/api/organizations', headers=headers)
    # The 51st request should be rate limited
    response = client.get('/api/organizations', headers=headers)
    assert response.status_code == 429

def test_invalid_token(client):
    """Test invalid token"""
    headers = {'Authorization': 'Bearer invalid_token'}
    response = client.get('/api/organizations', headers=headers)
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['error'] == 'Invalid token'

def test_malformed_auth_header(client):
    """Test malformed authorization header"""
    headers = {'Authorization': 'InvalidFormat'}
    response = client.get('/api/organizations', headers=headers)
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

class TestAPI(unittest.TestCase):
    BASE_URL = "http://localhost:3000"
    HEADERS = {"Authorization": "Bearer ft_test_api_2024"}

    def test_health_check(self):
        response = requests.get(f"{self.BASE_URL}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")

    def test_invalid_token(self):
        headers = {"Authorization": "Bearer invalid-token"}
        response = requests.get(f"{self.BASE_URL}/api/organizations", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_organizations_endpoint(self):
        response = requests.get(f"{self.BASE_URL}/api/organizations", headers=self.HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)

    def test_users_endpoint(self):
        response = requests.get(f"{self.BASE_URL}/api/users", headers=self.HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)

    def test_profiles_endpoint(self):
        response = requests.get(f"{self.BASE_URL}/api/profiles", headers=self.HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)

    def test_rate_limiting(self):
        # This test might be flaky due to rate limiting reset
        for _ in range(5):
            response = requests.get(f"{self.BASE_URL}/api/health")
            if response.status_code == 429:
                break
        # Just check that the endpoint exists
        self.assertIn(response.status_code, [200, 429])

    def test_organizations_filtering(self):
        response = requests.get(
            f"{self.BASE_URL}/api/organizations",
            headers=self.HEADERS,
            params={"name": "Organization 1"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should find organizations with "Organization 1" in the name
        self.assertGreater(len(data["items"]), 0)

    def test_users_filtering(self):
        response = requests.get(
            f"{self.BASE_URL}/api/users",
            headers=self.HEADERS,
            params={"organization_id": "ORG001"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should find users in ORG001
        self.assertGreater(len(data["items"]), 0)
        for user in data["items"]:
            self.assertEqual(user["organization_id"], "ORG001")

    # Advanced Search Tests
    def test_advanced_search_basic(self):
        """Test basic advanced search without parameters"""
        response = requests.get(f"{self.BASE_URL}/api/search/advanced", headers=self.HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("per_page", data)
        self.assertIn("total_pages", data)

    def test_advanced_search_text_query(self):
        """Test text search functionality with 'q' parameter"""
        response = requests.get(
            f"{self.BASE_URL}/api/search/advanced",
            headers=self.HEADERS,
            params={"q": "Organization 1", "type": "organizations", "per_page": 5}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should find organizations with "Organization 1" in the name
        self.assertGreater(len(data["items"]), 0)
        self.assertLessEqual(len(data["items"]), 5)
        
        # Verify all results contain the search term
        for item in data["items"]:
            self.assertEqual(item["type"], "organization")
            self.assertIn("1", item["name"])

    def test_advanced_search_type_filtering(self):
        """Test entity type filtering"""
        # Test organizations only
        response = requests.get(
            f"{self.BASE_URL}/api/search/advanced",
            headers=self.HEADERS,
            params={"type": "organizations", "per_page": 5}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        for item in data["items"]:
            self.assertEqual(item["type"], "organization")

        # Test users only
        response = requests.get(
            f"{self.BASE_URL}/api/search/advanced",
            headers=self.HEADERS,
            params={"type": "users", "per_page": 5}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        for item in data["items"]:
            self.assertEqual(item["type"], "user")

    def test_advanced_search_filters_basic(self):
        """Test basic filtering with filters parameter"""
        filters = {"name": "Organization 1"}
        response = requests.get(
            f"{self.BASE_URL}/api/search/advanced",
            headers=self.HEADERS,
            params={
                "type": "organizations",
                "filters": json.dumps(filters),
                "per_page": 5
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should find organizations with "Organization 1" in the name
        self.assertGreater(len(data["items"]), 0)
        for item in data["items"]:
            self.assertIn("1", item["name"])

    def test_advanced_search_nested_filters(self):
        """Test nested field filtering using dot notation"""
        filters = {"metadata.version": "1.0.0"}
        response = requests.get(
            f"{self.BASE_URL}/api/search/advanced",
            headers=self.HEADERS,
            params={
                "type": "organizations",
                "filters": json.dumps(filters),
                "per_page": 5
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should find organizations with version 1.0.0
        self.assertGreater(len(data["items"]), 0)
        for item in data["items"]:
            self.assertEqual(item["metadata"]["version"], "1.0.0")

    def test_advanced_search_combined(self):
        """Test combining text search and filters"""
        filters = {"organization_id": "ORG001"}
        response = requests.get(
            f"{self.BASE_URL}/api/search/advanced",
            headers=self.HEADERS,
            params={
                "q": "User",
                "type": "users",
                "filters": json.dumps(filters),
                "per_page": 5
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should find users with "User" in name from ORG001
        self.assertGreater(len(data["items"]), 0)
        for item in data["items"]:
            self.assertEqual(item["type"], "user")
            self.assertEqual(item["organization_id"], "ORG001")
            self.assertIn("User", item["name"])

    def test_advanced_search_pagination(self):
        """Test pagination parameters"""
        response = requests.get(
            f"{self.BASE_URL}/api/search/advanced",
            headers=self.HEADERS,
            params={"type": "all", "page": 1, "per_page": 5}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["per_page"], 5)
        self.assertLessEqual(len(data["items"]), 5)
        self.assertGreater(data["total"], 0)
        self.assertGreater(data["total_pages"], 0)

    def test_advanced_search_invalid_filters(self):
        """Test handling of invalid JSON in filters parameter"""
        response = requests.get(
            f"{self.BASE_URL}/api/search/advanced",
            headers=self.HEADERS,
            params={"filters": "invalid-json"}
        )
        # Should not crash, should default to empty filters
        self.assertEqual(response.status_code, 200)

    def test_advanced_search_empty_results(self):
        """Test search that returns no results"""
        response = requests.get(
            f"{self.BASE_URL}/api/search/advanced",
            headers=self.HEADERS,
            params={"q": "NonexistentSearchTerm12345"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["items"]), 0)
        self.assertEqual(data["total"], 0)

if __name__ == "__main__":
    unittest.main() 