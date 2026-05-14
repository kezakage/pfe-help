"""
Celery tasks: build export artifacts (PDF / ZIP / GeoJSON / CSV) for a project.
"""
import csv
import io
import json
import zipfile

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone


@shared_task
def run_export_job(job_id: int):
    from .models import ExportJob

    try:
        job = ExportJob.objects.select_related("project", "project__resource").get(pk=job_id)
    except ExportJob.DoesNotExist:
        return

    job.status = ExportJob.Status.PROCESSING
    job.started_at = timezone.now()
    job.save(update_fields=["status", "started_at"])

    try:
        if job.format == ExportJob.Format.PDF:
            payload, filename = _build_pdf(job)
        elif job.format == ExportJob.Format.GEOJSON:
            payload, filename = _build_geojson(job)
        elif job.format == ExportJob.Format.CSV:
            payload, filename = _build_csv(job)
        else:  # ZIP fallback bundling everything
            payload, filename = _build_zip(job)

        job.file.save(filename, ContentFile(payload), save=False)
        job.status = ExportJob.Status.DONE
        job.finished_at = timezone.now()
        job.save(update_fields=["file", "status", "finished_at"])
    except Exception as exc:  # noqa: BLE001
        job.status = ExportJob.Status.FAILED
        job.error_message = str(exc)[:2000]
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])


# ---------- builders ----------

def _build_pdf(job) -> tuple[bytes, str]:
    """PDF/A-1b export via WeasyPrint (ISO 19005-1, Dublin Core XMP)."""
    from .services.pdf import render_project_pdf

    if not job.project:
        raise ValueError("PDF export requires a project")
    payload = render_project_pdf(job.project)
    return payload, f"export_{job.pk}.pdf"


def _build_geojson(job) -> tuple[bytes, str]:
    features = []
    if job.project and job.project.resource and job.project.resource.geo_point:
        res = job.project.resource
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [res.geo_point.x, res.geo_point.y],
            },
            "properties": {
                "id": res.pk,
                "name_fr": res.name_fr,
                "name_ar": res.name_ar,
                "wilaya": res.wilaya,
                "period": res.period,
                "type": res.architectural_type,
                "classification": res.classification_level,
            },
        })
    fc = {"type": "FeatureCollection", "features": features}
    return json.dumps(fc, ensure_ascii=False).encode("utf-8"), f"export_{job.pk}.geojson"


def _build_csv(job) -> tuple[bytes, str]:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["id", "name_fr", "wilaya", "period", "type", "classification", "lat", "lng"])
    if job.project and job.project.resource:
        r = job.project.resource
        writer.writerow([
            r.pk, r.name_fr, r.wilaya, r.period, r.architectural_type,
            r.classification_level,
            r.geo_point.y if r.geo_point else "",
            r.geo_point.x if r.geo_point else "",
        ])
    return out.getvalue().encode("utf-8"), f"export_{job.pk}.csv"


def _build_zip(job) -> tuple[bytes, str]:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # bundle pdf + geojson + csv
        pdf_bytes, _ = _build_pdf(job)
        zf.writestr("project.pdf", pdf_bytes)
        geojson_bytes, _ = _build_geojson(job)
        zf.writestr("project.geojson", geojson_bytes)
        csv_bytes, _ = _build_csv(job)
        zf.writestr("project.csv", csv_bytes)
    return buf.getvalue(), f"export_{job.pk}.zip"
