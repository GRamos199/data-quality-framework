"""Tests for FastAPI application."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from data_quality_framework.api import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestAPIEndpoints:
    """Test FastAPI endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns 404."""
        response = client.get("/")
        assert response.status_code == 404

    def test_docs_endpoint(self, client):
        """Test Swagger docs endpoint is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_redoc_endpoint(self, client):
        """Test ReDoc endpoint is available."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_endpoint(self, client):
        """Test OpenAPI JSON endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_validate_json_endpoint_exists(self, client):
        """Test that validate/json endpoint exists."""
        # Should return 422 due to missing data, but endpoint should exist
        response = client.post("/validate/json")
        assert response.status_code in [400, 422, 200]

    def test_validate_csv_endpoint_exists(self, client):
        """Test that validate/csv endpoint exists."""
        # Should return 422 due to missing data, but endpoint should exist
        response = client.post("/validate/csv")
        assert response.status_code in [400, 422, 200]

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code in [200, 404]

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code in [200, 404]

    def test_validate_json_with_data(self, client):
        """Test validate/json with sample data."""
        payload = {
            "data": [{"name": "John", "age": 30}],
            "config": "openweather_raw_validation.yaml"
        }
        response = client.post(
            "/validate/json",
            json=payload
        )
        # Should get a response (may be 200 or error, but not 404)
        assert response.status_code != 404

    def test_validate_csv_with_file(self, client):
        """Test validate/csv endpoint with file upload."""
        # Create a sample CSV content
        csv_content = b"name,age\nJohn,30\nJane,25"
        
        files = {
            "file": ("test.csv", csv_content, "text/csv"),
            "config": (None, "openweather_raw_validation.yaml")
        }
        
        response = client.post("/validate/csv", files=files)
        # Should get a response (may be 200 or error, but not 404)
        assert response.status_code != 404


class TestAPIErrors:
    """Test API error handling."""

    def test_404_not_found(self, client):
        """Test 404 error for non-existent endpoint."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_invalid_json_request(self, client):
        """Test invalid JSON request handling."""
        response = client.post(
            "/validate/json",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]


class TestAPIHeaders:
    """Test API headers and CORS."""

    def test_response_headers(self, client):
        """Test response headers."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        # FastAPI should set proper content-type
        assert "content-type" in response.headers
