"""
Generate placeholder images for each seeded project so the demo UI looks
alive on the gallery, project detail, and media annotation pages.

Each image is synthesized with PIL — no binary assets committed to the repo,
no external downloads. The image carries the monument name, period, and
classification level, on a color scheme keyed to the period.

Usage:
    python manage.py seed_media
        [--per-project 3]   number of images to generate per project
        [--clear]           wipe existing seeded media (caption starts with "[seed]") before re-creating
"""
from __future__ import annotations

import hashlib
import io
import textwrap

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from apps.heritage.models import HeritageResource, Project
from apps.media.models import Media


# Color palette per period — picks one (bg, accent) tuple per resource period.
PERIOD_PALETTE = {
    "prehistoric": ((58, 39, 19), (210, 168, 100)),     # cave brown + ochre
    "numidian":    ((75, 53, 30), (220, 180, 110)),     # bronze
    "roman":       ((110, 26, 22), (240, 200, 110)),    # terracotta + gold
    "medieval":    ((42, 60, 90), (200, 180, 120)),     # zellige blue + sand
    "ottoman":     ((36, 80, 76), (210, 184, 140)),     # tile green + ivory
    "colonial":    ((84, 70, 62), (220, 200, 168)),     # sepia
    "contemporary":((44, 44, 50), (210, 210, 220)),     # neutral slate
    "other":       ((64, 50, 40), (220, 200, 170)),
}

W, H = 1200, 800  # large enough for a hero image, small enough to ship many


def _font(size: int) -> ImageFont.ImageFont:
    """Try a few common fonts the Linux container is likely to have; fall back to default."""
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_postcard(resource: HeritageResource, index: int) -> bytes:
    """Generate a deterministic placeholder image for (resource, index)."""
    period_key = (resource.period or "other").lower()
    bg, accent = PERIOD_PALETTE.get(period_key, PERIOD_PALETTE["other"])

    # Use a hash so each (resource, index) pair gives a slightly different overlay,
    # which avoids looking like a copy-paste in the gallery.
    h = int(hashlib.md5(f"{resource.pk}-{index}".encode()).hexdigest(), 16)
    offset_x = (h % 80) - 40
    offset_y = ((h >> 8) % 80) - 40

    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    # Geometric backdrop: 3 staggered rectangles in the accent color
    for i in range(3):
        x0 = 80 + i * 60 + offset_x
        y0 = 80 + i * 30 + offset_y
        x1 = x0 + 900
        y1 = y0 + 540
        a = 30 + i * 20
        overlay = Image.new("RGBA", (x1 - x0, y1 - y0), (*accent, a))
        img.paste(overlay, (x0, y0), overlay)

    # Title band at the bottom
    band_h = 200
    band = Image.new("RGBA", (W, band_h), (0, 0, 0, 170))
    img.paste(band, (0, H - band_h), band)

    title = resource.name_fr
    subtitle = f"{resource.wilaya} — {resource.get_period_display()}"
    classification = f"Classement : {resource.get_classification_level_display()}"
    caption = f"Photo de démonstration — Vue {index + 1}"

    # Layout: title (big) | subtitle | classification
    title_font = _font(56)
    sub_font = _font(28)
    small_font = _font(20)

    # Wrap title to two lines if needed
    lines = textwrap.wrap(title, width=24) or [title]
    y = H - band_h + 24
    for line in lines[:2]:
        draw.text((48, y), line, fill=(255, 255, 255), font=title_font)
        y += 60
    draw.text((48, H - 72), subtitle, fill=accent, font=sub_font)
    draw.text((48, H - 36), classification, fill=(220, 220, 220), font=small_font)
    draw.text((W - 360, H - 36), caption, fill=(180, 180, 180), font=small_font)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82, optimize=True)
    return buf.getvalue()


class Command(BaseCommand):
    help = "Seed placeholder images for each seeded project (PIL-generated, no external assets)."

    def add_arguments(self, parser):
        parser.add_argument("--per-project", type=int, default=3,
                            help="Number of placeholder images to generate per project (default: 3).")
        parser.add_argument("--clear", action="store_true",
                            help="Delete previously seeded media (caption starts with '[seed]') first.")

    def handle(self, *args, **options):
        per = options["per_project"]

        if options["clear"]:
            deleted, _ = Media.objects.filter(caption__startswith="[seed]").delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} previously-seeded media row(s)."))

        projects = Project.objects.select_related("resource", "created_by").all()
        if not projects.exists():
            self.stderr.write(self.style.ERROR(
                "No projects found. Run `python manage.py seed_projects` first."
            ))
            return

        total = 0
        for project in projects:
            resource = project.resource
            uploader = project.created_by
            if not resource or not uploader:
                continue

            # Skip if this project already has seeded images (idempotent).
            existing = project.media.filter(caption__startswith="[seed]").count()
            need = max(0, per - existing)
            if need == 0:
                self.stdout.write(f"  · {project.title} — already has {existing} seeded image(s), skipping.")
                continue

            for i in range(existing, existing + need):
                data = _render_postcard(resource, i)
                filename = f"seed-{project.pk}-{i + 1}.jpg"
                media = Media(
                    project=project,
                    uploader=uploader,
                    media_type=Media.Type.IMAGE,
                    mime_type="image/jpeg",
                    size_bytes=len(data),
                    width=W,
                    height=H,
                    caption=f"[seed] {resource.name_fr} — vue {i + 1}",
                    license="CC-BY-SA 4.0 (image générée pour la démo)",
                    # Skip the AI pipeline on seed images so we don't spawn celery jobs
                    # that try to classify a synthetic placeholder.
                    ai_status=Media.AiStatus.SKIPPED,
                )
                media.file.save(filename, ContentFile(data), save=True)
                total += 1

            self.stdout.write(self.style.SUCCESS(
                f"  ✓ {project.title} — +{need} image(s) (total {existing + need})"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Done — {total} new placeholder image(s) created."
        ))
