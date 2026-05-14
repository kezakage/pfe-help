"""
Verify PDF/A-1b export: format conformance + Dublin Core XMP metadata.

These tests render an actual PDF using WeasyPrint and inspect the
result with pikepdf — no mocks. They are a contract test for the
ISO 19005-1 + Dublin Core requirements from the project specification.
"""
import io

import pytest

from apps.exports.services.pdf import render_project_pdf
from apps.exports.services.tiptap import tiptap_to_html


pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Tiptap → HTML
# ---------------------------------------------------------------------------
def test_tiptap_renders_paragraph_and_heading():
    doc = {
        "type": "doc",
        "content": [
            {"type": "heading", "attrs": {"level": 2},
             "content": [{"type": "text", "text": "Histoire"}]},
            {"type": "paragraph",
             "content": [{"type": "text", "text": "Fondée au "},
                         {"type": "text", "text": "Xe siècle",
                          "marks": [{"type": "bold"}]},
                         {"type": "text", "text": "."}]},
        ],
    }
    html = tiptap_to_html(doc)
    assert '<h2 class="tt-h2">Histoire</h2>' in html
    assert '<strong class="tt-strong">Xe siècle</strong>' in html


def test_tiptap_handles_empty_doc():
    assert tiptap_to_html(None) == ""
    assert tiptap_to_html({}) == ""


def test_tiptap_escapes_html_in_text():
    doc = {"type": "doc", "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "<script>x</script>"}]},
    ]}
    html = tiptap_to_html(doc)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


# ---------------------------------------------------------------------------
# PDF/A render — full integration
# ---------------------------------------------------------------------------
@pytest.fixture
def project_with_page(db, project_published):
    """Add one page with real Tiptap content to the published project."""
    from apps.pages.models import Page, PageVersion

    page = Page.objects.create(
        project=project_published, title="Présentation", position=0,
    )
    version = PageVersion.objects.create(
        page=page, version_number=1,
        author=project_published.created_by,
        status=PageVersion.Status.PUBLISHED,
        content_json={
            "type": "doc",
            "content": [
                {"type": "heading", "attrs": {"level": 2},
                 "content": [{"type": "text", "text": "Présentation"}]},
                {"type": "paragraph",
                 "content": [{"type": "text",
                              "text": "Fixture text for PDF render."}]},
            ],
        },
    )
    page.current_version = version
    page.save()
    return project_published


def test_render_produces_pdf_a1b(project_with_page):
    """Output must start with PDF magic bytes and declare PDF/A-1b."""
    import pikepdf

    pdf = render_project_pdf(project_with_page)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000  # not an empty stub

    with pikepdf.open(io.BytesIO(pdf)) as doc:
        meta = doc.open_metadata()
        # PDF/A part + conformance — required by ISO 19005-1
        assert meta.get("{http://www.aiim.org/pdfa/ns/id/}part") == "1"
        assert meta.get("{http://www.aiim.org/pdfa/ns/id/}conformance") == "B"
        # OutputIntent must reference an ICC profile
        assert "/OutputIntents" in doc.Root
        oi = doc.Root.OutputIntents[0]
        assert str(oi.S) == "/GTS_PDFA1"


def test_render_embeds_dublin_core(project_with_page):
    """Required Dublin Core fields must appear in the XMP packet."""
    import pikepdf

    pdf = render_project_pdf(project_with_page)
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        meta = doc.open_metadata()
        DC = "http://purl.org/dc/elements/1.1/"
        title = str(meta.get(f"{{{DC}}}title", ""))
        assert "PatrimoineHub" in title
        assert str(meta.get(f"{{{DC}}}publisher", "")).startswith("PatrimoineHub")
        # Multi-valued fields come back as list-like proxies
        contributors = meta.get(f"{{{DC}}}contributor")
        assert contributors is not None and len(list(contributors)) >= 1
        identifier = str(meta.get(f"{{{DC}}}identifier", ""))
        assert identifier.startswith("patrimoinehub:project:")
        assert str(meta.get(f"{{{DC}}}coverage", "")).endswith("Algérie")
        assert str(meta.get(f"{{{DC}}}type", "")) == "Text"
        assert str(meta.get(f"{{{DC}}}format", "")) == "application/pdf"


def test_render_handles_project_without_pages(project_published):
    """A project with no pages should still produce a (cover-only) PDF."""
    pdf = render_project_pdf(project_published)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000
