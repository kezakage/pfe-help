"""
Elasticsearch documents for the heritage app.

`HeritageResourceDocument` mirrors `HeritageResource` into an ES index with
language-aware analyzers (French + Arabic), keyword fields for facetting,
geo_point for spatial queries, and a completion field for autocomplete.

django-elasticsearch-dsl auto-syncs on model save/delete via signals
(ELASTICSEARCH_DSL_AUTOSYNC=True in settings).
"""
from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry

from .models import HeritageResource

# Single index for heritage resources. Replicas=0 fits a single-node dev cluster.
heritage_index = Index("heritage_resources")
heritage_index.settings(number_of_shards=1, number_of_replicas=0)


@registry.register_document
@heritage_index.doc_type
class HeritageResourceDocument(Document):
    """ES document for HeritageResource — multilang text + facets + geo + suggest."""

    # Core text fields with language analyzers + a `.keyword` sub-field for
    # exact/sortable access where needed.
    name_fr = fields.TextField(
        analyzer="french",
        fields={
            "keyword": fields.KeywordField(),
            "suggest": fields.CompletionField(),  # autocomplete
        },
    )
    name_ar = fields.TextField(
        analyzer="arabic",
        fields={"keyword": fields.KeywordField()},
    )
    description = fields.TextField(analyzer="french")

    # Faceted/filterable enums — keyword so they aggregate cleanly.
    period = fields.KeywordField()
    architectural_type = fields.KeywordField()
    classification_level = fields.KeywordField()

    # Location: keyword for facets + text for fuzzy match.
    wilaya = fields.KeywordField(
        fields={"text": fields.TextField(analyzer="french")},
    )
    commune = fields.TextField(analyzer="french")

    # Spatial — generated from PostGIS Point.
    location = fields.GeoPointField()

    created_at = fields.DateField()
    updated_at = fields.DateField()

    class Django:
        model = HeritageResource
        # Drives auto-sync: any save() touching one of these triggers a re-index.
        fields = []  # we declare fields explicitly above

    # ---- prepare_<field> hooks --------------------------------------------
    def prepare_location(self, instance):
        if instance.geo_point:
            return {"lat": instance.geo_point.y, "lon": instance.geo_point.x}
        return None

    def prepare_name_fr(self, instance):
        # CompletionField needs `input` keys for suggestions; here we let ES
        # auto-extract from the text by passing the raw string. The completion
        # sub-field is populated automatically via fields={"suggest": ...}.
        return instance.name_fr or ""

    # Ensure related-model changes don't silently leave the index stale.
    def get_queryset(self):
        return super().get_queryset().select_related()

    def get_instances_from_related(self, related_instance):  # pragma: no cover
        # No reverse FK we care about right now; placeholder for future use
        # (e.g. re-index a resource when a Project metadata changes).
        return None
