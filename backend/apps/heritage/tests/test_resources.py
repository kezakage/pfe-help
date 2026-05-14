"""HeritageResource list / GeoJSON / write permissions."""
import pytest

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Public read access
# ---------------------------------------------------------------------------
def test_anonymous_can_list_resources(api_client, resource_unesco, resource_national):
    res = api_client.get("/api/v1/heritage/resources/")
    assert res.status_code == 200
    body = res.json()
    items = body if isinstance(body, list) else body.get("results", [])
    names = {r["name_fr"] for r in items}
    assert "Casbah de test" in names
    assert "Mosquée de test" in names


def test_geojson_returns_feature_collection(api_client, resource_unesco, resource_national):
    res = api_client.get("/api/v1/heritage/resources/geojson/")
    assert res.status_code == 200
    body = res.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 2
    f = body["features"][0]
    assert f["type"] == "Feature"
    assert f["geometry"]["type"] == "Point"
    coords = f["geometry"]["coordinates"]
    assert len(coords) == 2  # [lng, lat]
    # All seeded fixtures have a classification level
    assert "classification_level" in f["properties"]


def test_geojson_excludes_resources_without_geo_point(api_client, resource_unesco):
    # Wipe geo_point on the existing resource — it must disappear from the FC
    resource_unesco.geo_point = None
    resource_unesco.save()
    res = api_client.get("/api/v1/heritage/resources/geojson/")
    assert res.status_code == 200
    assert res.json()["features"] == []


def test_geojson_honors_period_filter(api_client, resource_unesco, resource_national):
    # resource_unesco is OTTOMAN, resource_national is MEDIEVAL
    res = api_client.get("/api/v1/heritage/resources/geojson/?period=ottoman")
    assert res.status_code == 200
    feats = res.json()["features"]
    assert len(feats) == 1
    assert feats[0]["properties"]["period"] == "ottoman"


# ---------------------------------------------------------------------------
# Write permissions
# ---------------------------------------------------------------------------
def _payload():
    return {
        "name_fr": "Nouveau monument",
        "period": "ottoman",
        "architectural_type": "mosque",
        "wilaya": "Alger",
        "classification_level": "national",
        "longitude": 3.06,
        "latitude": 36.78,
    }


def test_anonymous_cannot_create_resource(api_client):
    res = api_client.post("/api/v1/heritage/resources/", _payload(), format="json")
    assert res.status_code in (401, 403)


def test_researcher_cannot_create_resource(auth_client, researcher_user):
    client = auth_client(researcher_user)
    res = client.post("/api/v1/heritage/resources/", _payload(), format="json")
    assert res.status_code == 403


def test_pending_expert_cannot_create_resource(auth_client, pending_expert):
    client = auth_client(pending_expert)
    res = client.post("/api/v1/heritage/resources/", _payload(), format="json")
    assert res.status_code == 403


def test_validated_expert_can_create_resource(auth_client, expert_user):
    client = auth_client(expert_user)
    res = client.post("/api/v1/heritage/resources/", _payload(), format="json")
    assert res.status_code == 201, res.content
    assert res.json()["name_fr"] == "Nouveau monument"


def test_admin_can_create_resource(auth_client, admin_user):
    client = auth_client(admin_user)
    res = client.post("/api/v1/heritage/resources/", _payload(), format="json")
    assert res.status_code == 201, res.content
