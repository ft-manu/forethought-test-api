from locust import HttpUser, task, between
import random

class TestAPIUser(HttpUser):
    wait_time = between(1, 3)
    token = "ft_test_api_2024"
    
    def on_start(self):
        """Set up headers for all requests"""
        self.headers = {
            'Authorization': f'Bearer {self.token}'
        }
    
    @task(3)
    def get_organizations(self):
        """Test getting all organizations"""
        self.client.get('/api/organizations', headers=self.headers)
    
    @task(2)
    def get_specific_organization(self):
        """Test getting a specific organization"""
        org_id = f"ORG{random.randint(1, 10):03d}"
        self.client.get(f'/api/organizations/{org_id}', headers=self.headers)
    
    @task(1)
    def get_filtered_organizations(self):
        """Test getting filtered organizations"""
        org_types = ['enterprise', 'startup']
        org_type = random.choice(org_types)
        self.client.get(f'/api/organizations?type={org_type}', headers=self.headers)
    
    @task(1)
    def get_nested_data(self):
        """Test getting deeply nested data"""
        org_id = f"ORG{random.randint(1, 10):03d}"
        self.client.get(
            f'/api/organizations/{org_id}/headquarters/address/coordinates/geographic/region/classification/population/density/measurement/conversion',
            headers=self.headers
        )
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        self.client.get('/health')
    
    @task(1)
    def get_metrics(self):
        """Test metrics endpoint"""
        self.client.get('/metrics') 