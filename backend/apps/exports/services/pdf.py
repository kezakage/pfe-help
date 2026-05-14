"""
Project → PDF/A-1b generation using WeasyPrint.

The output complies with ISO 19005-1 (PDF/A-1b) and embeds Dublin Core
metadata in its XMP packet, as required by the project specification.
"""
from __future__ import annotations

import base64
import io
import logging
import mimetypes
from pathlib import Path

from django.template.loader import render_to_string
from django.utils import timezone

from apps.heritage.models import Project

from .tiptap import tiptap_to_html


logger = logging.getLogger(__name__)


_STYLESHEET_PATH = (
    Path(__file__).resolve().parent.parent / "static" / "exports" / "pdf" / "project.css"
)


def _stylesheet() -> str:
    """Read the print stylesheet from disk and return it for inlining."""
    return _STYLESHEET_PATH.read_text(encoding="utf-8")


def render_project_pdf(project: Project) -> bytes:
    """
    Build an archival-quality PDF/A-1b for a Project.

    The function gathers the project, its resource, ordered pages (using
    each page's `current_version`) and members, transforms the Tiptap
    JSON into HTML, then asks WeasyPrint to write a PDF/A-1b document
    with Dublin Core XMP metadata embedded.
    """
    # Lazy import: WeasyPrint pulls native libs at import time. Keeping the
    # import inside the function lets unit tests stub it cleanly.
    from weasyprint import HTML

    resource = project.resource

    members = list(
        project.memberships.select_related("user").order_by("project_role")
    )
    contributors_csv = ", ".join(m.user.full_name for m in members)

    pages = []
    for page in project.pages.all().order_by("position"):
        cv = page.current_version
        pages.append({
            "title": page.title,
            "html_body": tiptap_to_html(cv.content_json) if cv else "",
        })

    gallery = _build_image_gallery(project)

    html_string = render_to_string(
        "exports/pdf/project.html",
        {
            "project": project,
            "resource": resource,
            "members": members,
            "contributors_csv": contributors_csv,
            "pages": pages,
            "gallery": gallery,
            "stylesheet": _stylesheet(),
            "generated_at": timezone.now(),
        },
    )

    buffer = io.BytesIO()
    HTML(string=html_string).write_pdf(
        target=buffer,
        # PDF/A-1b — ISO 19005-1, level B (visual conformance).
        pdf_variant="pdf/a-1b",
    )

    # Enrich XMP metadata with Dublin Core terms WeasyPrint doesn't map
    # automatically (publisher, contributor, identifier, rights, coverage,
    # subject, language, type, format).
    return _enrich_dublin_core(
        buffer.getvalue(),
        project=project,
        resource=resource,
        contributors_csv=contributors_csv,
    )


def _build_image_gallery(project: Project, *, max_items: int = 12) -> list[dict]:
    """
    Read each image Media attached to the project and embed it as a base64
    data URL — WeasyPrint can render it without needing network access to
    the storage backend (works for both local and S3/MinIO).
    """
    from apps.media.models import Media

    items: list[dict] = []
    qs = (
        Media.objects.filter(project=project, media_type=Media.Type.IMAGE)
        .order_by("created_at")[:max_items]
    )
    for m in qs:
        try:
            with m.file.open("rb") as fh:
                data = fh.read()
        except Exception as exc:  # noqa: BLE001
            logger.warning("PDF gallery: skipping media %s (%s)", m.pk, exc)
            continue
        mime = m.mime_type or mimetypes.guess_type(m.file.name)[0] or "image/jpeg"
        items.append({
            "data_url": f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}",
            "caption": m.caption or "",
            "credit": m.license or "",
        })
    return items


def _enrich_dublin_core(
    pdf_bytes: bytes, *, project: Project, resource, contributors_csv: str
) -> bytes:
    """Open the PDF with pikepdf and add the missing Dublin Core terms."""
    import pikepdf

    src = io.BytesIO(pdf_bytes)
    out = io.BytesIO()
    with pikepdf.open(src) as doc:
        with doc.open_metadata() as meta:
            # dc:* (Dublin Core elements)
            meta["dc:publisher"] = (
                "PatrimoineHub — Plateforme nationale algérienne du patrimoine"
            )
            meta["dc:contributor"] = [
                name.strip() for name in contributors_csv.split(",") if name.strip()
            ] or [project.created_by.full_name]
            meta["dc:subject"] = [
                resource.name_fr,
                resource.wilaya,
                str(resource.get_period_display()),
                str(resource.get_architectural_type_display()),
            ]
            meta["dc:identifier"] = f"patrimoinehub:project:{project.id}"
            meta["dc:rights"] = (
                f"© {timezone.now().year} PatrimoineHub. Tous droits réservés."
            )
            meta["dc:coverage"] = f"{resource.wilaya}, Algérie"
            meta["dc:type"] = "Text"
            meta["dc:format"] = "application/pdf"
            meta["dc:language"] = ["fr", "ar"] if resource.name_ar else ["fr"]

        doc.save(out)
    return out.getvalue()
