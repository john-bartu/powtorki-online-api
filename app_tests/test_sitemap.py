from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.database import models
from app.constants import TaxonomyTypes

client = TestClient(app)

def test_get_sitemap_subjects():
    response = client.get("/sitemap/subjects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "subjectId" in data[0]

def test_get_sitemap_taxonomies():
    response = client.get("/sitemap/taxonomies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "subjectId" in data[0]
        assert "taxonomyId" in data[0]

def test_get_sitemap_pages():
    response = client.get("/sitemap/pages")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "subjectId" in data[0]
        assert "taxonomyId" in data[0]
        assert "pageSubTypeId" in data[0]
        assert "pageId" in data[0]
