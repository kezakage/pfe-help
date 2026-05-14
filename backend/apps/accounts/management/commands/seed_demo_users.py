"""
Create demo users covering all roles + a realistic mix of validated experts,
researchers, and pending validations for the admin dashboard.

Usage:
    python manage.py seed_demo_users
"""
from django.core.management.base import BaseCommand

from apps.accounts.models import Discipline, User


DEMO = [
    # ---------- Admin ----------
    {
        "email": "admin@patrimoine.dz", "password": "Admin12345!",
        "first_name": "Admin", "last_name": "Plateforme",
        "role": User.Role.ADMIN, "status": User.Status.ACTIVE,
        "is_staff": True, "is_superuser": True,
        "institution_name": "Ministère de la Culture (Algérie)",
        "disciplines": [],
    },

    # ---------- Validated experts (one per major discipline) ----------
    {
        "email": "expert@patrimoine.dz", "password": "Expert12345!",
        "first_name": "Yacine", "last_name": "Belkacem",
        "role": User.Role.EXPERT, "status": User.Status.ACTIVE,
        "institution_name": "École Polytechnique d'Architecture et d'Urbanisme (EPAU)",
        "bio": "Architecte spécialiste de la restauration du patrimoine ottoman algérois.",
        "disciplines": ["Architecture", "Histoire"],
    },
    {
        "email": "amina.belhadj@univ-alger.dz", "password": "Expert12345!",
        "first_name": "Amina", "last_name": "Belhadj",
        "role": User.Role.EXPERT, "status": User.Status.ACTIVE,
        "institution_name": "Université d'Alger 2 — Faculté des sciences humaines",
        "bio": "Historienne médiéviste, spécialiste de la dynastie zianide de Tlemcen.",
        "disciplines": ["Histoire"],
    },
    {
        "email": "hocine.mansouri@cnrpah.dz", "password": "Expert12345!",
        "first_name": "Hocine", "last_name": "Mansouri",
        "role": User.Role.EXPERT, "status": User.Status.ACTIVE,
        "institution_name": "CNRPAH — Centre National de Recherches Préhistoriques",
        "bio": "Archéologue, directeur de fouilles à Djémila et Timgad.",
        "disciplines": ["Archéologie", "Histoire"],
    },
    {
        "email": "leila.bouzid@univ-tlemcen.dz", "password": "Expert12345!",
        "first_name": "Leïla", "last_name": "Bouzid",
        "role": User.Role.EXPERT, "status": User.Status.ACTIVE,
        "institution_name": "Université Abou Bekr Belkaïd — Tlemcen",
        "bio": "Conservatrice du patrimoine, spécialiste de l'art mérinide.",
        "disciplines": ["Conservation", "Architecture"],
    },
    {
        "email": "karim.saadi@cnrpah.dz", "password": "Expert12345!",
        "first_name": "Karim", "last_name": "Saadi",
        "role": User.Role.EXPERT, "status": User.Status.ACTIVE,
        "institution_name": "CNRPAH",
        "bio": "Anthropologue, terrain au M'Zab et dans le Sud algérien.",
        "disciplines": ["Anthropologie", "Histoire"],
    },

    # ---------- Researchers (validated) ----------
    {
        "email": "chercheur@patrimoine.dz", "password": "Chercheur12345!",
        "first_name": "Amina", "last_name": "Hadjadj",
        "role": User.Role.RESEARCHER, "status": User.Status.ACTIVE,
        "institution_name": "Université de Constantine 3 — Salah Boubnider",
        "disciplines": ["Archéologie"],
    },
    {
        "email": "riad.hamdi@univ-oran.dz", "password": "Chercheur12345!",
        "first_name": "Riad", "last_name": "Hamdi",
        "role": User.Role.RESEARCHER, "status": User.Status.ACTIVE,
        "institution_name": "Université Oran 1 Ahmed Ben Bella",
        "disciplines": ["Urbanisme"],
    },

    # ---------- Pending validations (admin demo) ----------
    {
        "email": "samira.cherif@univ-batna.dz", "password": "Pending12345!",
        "first_name": "Samira", "last_name": "Chérif",
        "role": User.Role.EXPERT, "status": User.Status.PENDING,
        "institution_name": "Université Batna 1 — Hadj Lakhdar",
        "bio": "Doctorante en archéologie romaine, candidate au statut d'expert.",
        "disciplines": ["Archéologie"],
    },
    {
        "email": "mohamed.zerouali@gmail.com", "password": "Pending12345!",
        "first_name": "Mohamed", "last_name": "Zerouali",
        "role": User.Role.EXPERT, "status": User.Status.PENDING,
        "institution_name": "Indépendant",
        "bio": "Architecte praticien, demande de validation expert en cours.",
        "disciplines": ["Architecture"],
    },
]


class Command(BaseCommand):
    help = "Seed 10 demo users (admin, experts, researchers, pending)."

    def handle(self, *args, **options):
        created_count = 0
        for entry in DEMO:
            disc_names = entry.pop("disciplines", [])
            password = entry.pop("password")
            user, created = User.objects.update_or_create(
                email=entry["email"], defaults=entry,
            )
            user.set_password(password)
            user.save()
            for name in disc_names:
                d = Discipline.objects.filter(name_fr=name).first()
                if d:
                    user.disciplines.add(d)
            if created:
                created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} {user.email} ({user.role}/{user.status})"
            ))
        self.stdout.write(self.style.SUCCESS(
            f"Done — {len(DEMO)} users ({created_count} new)."
        ))
