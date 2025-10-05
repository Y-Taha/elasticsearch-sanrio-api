import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import CharacterCreate
from app.models import CHAR_INDEX
from app.elastic_client import get_es_client

client = TestClient(app)
es = get_es_client()


# ---------- FIXTURE: Setup Elasticsearch Index ----------
@pytest.fixture(scope="module", autouse=True)
def setup_index():
    """Ensure index exists before tests run."""
    # Use modern ES syntax to avoid deprecation warnings
    es.options(ignore_status=[400, 404]).indices.delete(index=CHAR_INDEX)
    es.indices.create(
        index=CHAR_INDEX,
        body={
            "mappings": {
                "properties": {
                    "name": {"type": "text"},
                    "franchise": {"type": "keyword"},
                    "species": {"type": "keyword"},
                    "debut_year": {"type": "integer"},
                    "tags": {"type": "keyword"},
                    "description": {"type": "text"},
                }
            }
        },
    )
    yield
    es.options(ignore_status=[400, 404]).indices.delete(index=CHAR_INDEX)


# ---------- UNIT TESTS ----------

def test_character_schema_valid():
    """Test CharacterCreate schema validation with correct data."""
    char = CharacterCreate(
        name="Hello Kitty",
        franchise="Sanrio",
        species="Cat",
        debut_year=1974,
        tags=["cute", "classic"],
        description="A sweet cat with a bow.",
    )
    assert char.name == "Hello Kitty"
    assert char.debut_year == 1974


def test_character_schema_invalid_year():
    """Test schema rejects invalid debut_year."""
    with pytest.raises(ValueError):
        CharacterCreate(name="Keroppi", debut_year=2200)  # invalid future year


# ---------- INTEGRATION TESTS ----------

@pytest.fixture
def sample_character():
    return {
        "name": "Cinnamoroll",
        "franchise": "Sanrio",
        "species": "Puppy",
        "debut_year": 2001,
        "tags": ["cute", "fluffy"],
        "description": "A white puppy with long ears that enable him to fly.",
    }


def test_create_character(sample_character):
    """Create a new character and check Elasticsearch indexing."""
    res = client.post("/characters", json=sample_character)
    assert res.status_code in (200, 201)
    data = res.json()
    assert "id" in data
    assert data["name"] == sample_character["name"]


def test_get_character(sample_character):
    """Verify character retrieval works correctly."""
    created = client.post("/characters", json=sample_character).json()
    char_id = created["id"]
    res = client.get(f"/characters/{char_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == sample_character["name"]


def test_update_character(sample_character):
    """Ensure updating a character works."""
    created = client.post("/characters", json=sample_character).json()
    char_id = created["id"]
    updated = {**sample_character, "description": "Updated description"}
    res = client.put(f"/characters/{char_id}", json=updated)
    assert res.status_code == 200
    assert res.json()["description"] == "Updated description"


def test_search_character(sample_character):
    """Check search endpoint supports fuzzy search and filtering."""
    client.post("/characters", json=sample_character)

    # Force Elasticsearch to refresh the index before searching
    es.indices.refresh(index=CHAR_INDEX)

    res = client.get("/search", params={"q": "Cinnamoroll", "fuzzy": "true"})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1


def test_delete_character(sample_character):
    """Ensure character can be deleted."""
    created = client.post("/characters", json=sample_character).json()
    char_id = created["id"]
    res = client.delete(f"/characters/{char_id}")
    assert res.status_code == 200

    # Verify it's gone
    confirm = client.get(f"/characters/{char_id}")
    assert confirm.status_code == 404
