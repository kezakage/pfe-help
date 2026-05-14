"""
Tests for the Elasticsearch-backed search/suggest endpoints.

We don't talk to a real ES cluster here — instead we monkeypatch
`HeritageResourceDocument.search` to return a chainable fake `Search`
object whose `.execute()` yields a predictable response.

The chainable API (`.query().filter()...[start:stop]`) is reproduced
just well enough that the view code under test can build its query
without raising.
"""
import types

import pytest

from apps.heritage.documents import HeritageResourceDocument

pytestmark = pytest.mark.django_db


# --- Fake Search/Response factory ------------------------------------------
class _FakeAggBucket:
    def __init__(self, key, count):
        self.key = key
        self.doc_count = count


class _FakeAgg:
    def __init__(self, buckets):
        self.buckets = [_FakeAggBucket(**b) for b in buckets]


class _FakeAggregations(dict):
    def __getitem__(self, k):
        return super().__getitem__(k)


class _FakeHitMeta:
    def __init__(self, id, score, highlight=None):
        self.id = str(id)
        self.score = score
        if highlight is not None:
            self.highlight = types.SimpleNamespace(to_dict=lambda: highlight)


class _FakeHit:
    def __init__(self, id, src, score=1.0, highlight=None):
        self._src = src
        self.meta = _FakeHitMeta(id, score, highlight=highlight)

    def to_dict(self):
        return self._src


class _FakeHits:
    def __init__(self, total, hits):
        self.total = types.SimpleNamespace(value=total)
        self._hits = hits

    def __iter__(self):
        return iter(self._hits)


class _FakeSuggestOption:
    def __init__(self, id, text, score=1.0):
        self._id = str(id)
        self.text = text
        self._score = score


class _FakeResponse:
    def __init__(self, hits, aggs, suggest=None):
        self.hits = _FakeHits(len(hits), hits)
        self.aggregations = _FakeAggregations(aggs)
        if suggest is not None:
            ns = types.SimpleNamespace()
            ns.name_suggest = [types.SimpleNamespace(options=suggest)]
            self.suggest = ns

    # iteration over a Search response yields hits
    def __iter__(self):
        return iter(self.hits)


class _FakeSearch:
    """Minimal chainable stand-in for elasticsearch_dsl.Search."""
    def __init__(self, response):
        self._response = response
        self.aggs = types.SimpleNamespace(bucket=lambda *a, **kw: None)

    def query(self, *a, **kw): return self
    def filter(self, *a, **kw): return self
    def highlight_options(self, *a, **kw): return self
    def highlight(self, *a, **kw): return self
    def suggest(self, *a, **kw): return self
    def __getitem__(self, _slice): return self
    def execute(self): return self._response


def _stub_search_factory(response):
    def _factory():
        return _FakeSearch(response)
    return _factory


# --- /search/ endpoint ------------------------------------------------------
def test_es_search_returns_results_facets_highlights(api_client, monkeypatch):
    fake = _FakeResponse(
        hits=[
            _FakeHit(
                id=1,
                src={
                    "name_fr": "Casbah d'Alger", "name_ar": "قصبة الجزائر",
                    "description": "Médina ottomane", "period": "ottoman",
                    "architectural_type": "casbah", "classification_level": "unesco",
                    "wilaya": "Alger", "commune": "Casbah",
                    "location": {"lat": 36.78, "lon": 3.06},
                },
                score=10.5,
                highlight={"name_fr": ["<mark>Casbah</mark> d'Alger"]},
            ),
        ],
        aggs={
            "period": _FakeAgg([{"key": "ottoman", "count": 1}]),
            "architectural_type": _FakeAgg([{"key": "casbah", "count": 1}]),
            "classification_level": _FakeAgg([{"key": "unesco", "count": 1}]),
            "wilaya": _FakeAgg([{"key": "Alger", "count": 1}]),
        },
    )
    monkeypatch.setattr(HeritageResourceDocument, "search", _stub_search_factory(fake))

    res = api_client.get("/api/v1/heritage/resources/search/?q=casbah")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["results"][0]["id"] == 1
    assert body["results"][0]["highlight"]["name_fr"] == ["<mark>Casbah</mark> d'Alger"]
    assert body["facets"]["period"] == [{"key": "ottoman", "count": 1}]
    assert body["facets"]["wilaya"] == [{"key": "Alger", "count": 1}]


def test_es_search_returns_503_when_es_unavailable(api_client, monkeypatch):
    class _Boom(_FakeSearch):
        def execute(self): raise RuntimeError("no connection")

    def _factory():
        return _Boom(None)
    monkeypatch.setattr(HeritageResourceDocument, "search", _factory)

    res = api_client.get("/api/v1/heritage/resources/search/?q=x")
    assert res.status_code == 503
    assert res.json()["error"] == "search_unavailable"


def test_es_search_paginates(api_client, monkeypatch):
    fake = _FakeResponse(
        hits=[],
        aggs={k: _FakeAgg([]) for k in
              ("period", "architectural_type", "classification_level", "wilaya")},
    )
    monkeypatch.setattr(HeritageResourceDocument, "search", _stub_search_factory(fake))

    res = api_client.get("/api/v1/heritage/resources/search/?page=3&size=5")
    assert res.status_code == 200
    body = res.json()
    assert body["page"] == 3
    assert body["size"] == 5


# --- /suggest/ endpoint -----------------------------------------------------
def test_suggest_returns_options(api_client, monkeypatch):
    fake = _FakeResponse(
        hits=[],
        aggs={},
        suggest=[
            _FakeSuggestOption(id=1, text="Casbah d'Alger", score=2.0),
            _FakeSuggestOption(id=2, text="Casbah de Béjaïa", score=1.5),
        ],
    )
    monkeypatch.setattr(HeritageResourceDocument, "search", _stub_search_factory(fake))

    res = api_client.get("/api/v1/heritage/resources/suggest/?q=Cas")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 2
    assert body[0] == {"id": 1, "text": "Casbah d'Alger", "score": 2.0}


def test_suggest_returns_empty_for_blank_query(api_client):
    res = api_client.get("/api/v1/heritage/resources/suggest/?q=")
    assert res.status_code == 200
    assert res.json() == []
