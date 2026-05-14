"""
Seed 10 enriched projects on the most iconic monuments. Each project gets:
  - 4-5 sections (Pages) with realistic Tiptap content
  - 3+ members across different disciplines
  - 1-2 discussions (some open, some resolved, some conflicts)
  - A few votes on conflicts

Prereqs:
    python manage.py seed_heritage
    python manage.py seed_demo_users
    python manage.py loaddata apps/accounts/fixtures/disciplines.json

Usage:
    python manage.py seed_projects
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Discipline, User
from apps.discussions.models import ConflictVote, Discussion, Message
from apps.heritage.models import HeritageResource, Project, ProjectMember
from apps.pages.models import Page, PageVersion


def doc(*paragraphs):
    """Build a minimal Tiptap doc from a list of paragraph strings."""
    content = []
    for p in paragraphs:
        if p.startswith("# "):
            content.append({
                "type": "heading", "attrs": {"level": 2},
                "content": [{"type": "text", "text": p[2:]}],
            })
        else:
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": p}],
            })
    return {"type": "doc", "content": content}


# ---------------------------------------------------------------------------
# Page templates per resource (key = name_fr of HeritageResource)
# ---------------------------------------------------------------------------
PROJECT_BLUEPRINTS = {
    "Casbah d'Alger": {
        "title": "Documentation de la Casbah d'Alger",
        "description": "Projet collaboratif de documentation de la médina ottomane d'Alger, classée UNESCO en 1992.",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "La Casbah d'Alger est l'unique exemple en Afrique du Nord d'une médina ottomane préservant son tissu urbain originel sur près de 50 hectares en pente vers la mer.",
                "Inscrite sur la liste du patrimoine mondial de l'UNESCO en 1992, elle compte plus de 1 200 maisons traditionnelles, 17 mosquées, 7 zaouïas et plusieurs palais beylicaux.",
            ]),
            ("Histoire", [
                "# Histoire",
                "Fondée au Xe siècle par les Zirides sur les ruines de l'antique Icosium, la cité prend son visage actuel sous la régence ottomane (1516-1830).",
                "Le sultan Aroudj puis Khayr ad-Dîn Barberousse y établissent leur capitale, attirant artisans, marins et lettrés des deux rives de la Méditerranée.",
                "La conquête française en 1830 amorce une longue dégradation : éventrement de la basse Casbah, démolitions massives sous Haussmann, surpopulation au XXe siècle.",
            ]),
            ("Description architecturale", [
                "# Description architecturale",
                "Le tissu urbain s'organise selon un réseau de venelles en escalier (zenqa) reliant la marine à la citadelle (Dar es-Soltane).",
                "L'architecture domestique repose sur la maison à patio (wast ed-dar) à colonnades torses, plafonds en cèdre peint et carrelages tunisois.",
                "Les édifices religieux mêlent influences ottomane (Ketchaoua, El Djedid) et almoravide (Mosquée El Kebir).",
            ]),
            ("État de conservation", [
                "# État de conservation",
                "Plus de 30 % des bâtisses sont en ruine ou en péril selon le rapport UNESCO 2023. Programme PPSMVSS lancé en 2012, peu de réalisations concrètes.",
                "L'opération de restauration de la Mosquée Ketchaoua (2018) reste un exemple isolé de réussite.",
            ]),
            ("Sources", [
                "# Sources et bibliographie",
                "Klein H., Feuillets d'el-Djezaïr (1937) ; Missoum S., Alger à l'époque ottomane (2003) ; UNESCO, État de conservation 2023.",
            ]),
        ],
        "members": [
            ("expert@patrimoine.dz", "lead"),
            ("amina.belhadj@univ-alger.dz", "contributor"),
            ("hocine.mansouri@cnrpah.dz", "reviewer"),
            ("leila.bouzid@univ-tlemcen.dz", "contributor"),
        ],
        "status": "in_progress",
        "discussions": [
            {
                "title": "Datation exacte de la fondation ziride",
                "type": "general", "status": "open",
                "messages": [
                    ("amina.belhadj@univ-alger.dz", "La date traditionnelle de 960 mérite révision à la lumière des fouilles de la rue Bab El Oued."),
                    ("hocine.mansouri@cnrpah.dz", "D'accord, mais les céramiques retrouvées sont datables au plus tôt du XIe siècle."),
                ],
            },
        ],
    },

    "Djémila (Cuicul)": {
        "title": "Atlas archéologique de Djémila",
        "description": "Cartographie et documentation des édifices civils et religieux de l'ancienne Cuicul.",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "Djémila, l'antique Cuicul, est une colonie militaire romaine fondée à 900 m d'altitude au nord de Sétif, vers la fin du Ier siècle.",
                "Site classé UNESCO en 1982 pour son exceptionnel témoignage d'urbanisme romain en montagne.",
            ]),
            ("Histoire", [
                "# Histoire",
                "Fondée sous Nerva pour des vétérans de la IIIe légion Auguste, Cuicul devient un nœud commercial entre Cirta (Constantine) et Sitifis (Sétif).",
                "Au IVe siècle, la christianisation transforme le quartier sud avec la construction d'une basilique et d'un baptistère monumental.",
                "L'invasion vandale (430) puis l'arrivée arabe (VIIe s.) entraînent l'abandon progressif du site.",
            ]),
            ("Description architecturale", [
                "# Description architecturale",
                "Forum sévérien, théâtre adossé à la pente, thermes de Commode et grande basilique chrétienne forment l'épine dorsale du site.",
                "La maison de l'Âne et la maison d'Europe livrent les mosaïques les plus remarquables, exposées au musée du site.",
            ]),
            ("Bibliographie", [
                "# Sources",
                "Allais Y., Djémila (1938) ; Février P.-A., Djémila (1968) ; UNESCO File 191.",
            ]),
        ],
        "members": [
            ("hocine.mansouri@cnrpah.dz", "lead"),
            ("amina.belhadj@univ-alger.dz", "contributor"),
            ("samira.cherif@univ-batna.dz", "contributor"),
        ],
        "status": "published",
        "discussions": [],
    },

    "Timgad (Thamugadi)": {
        "title": "Plan urbanistique de Timgad",
        "description": "Étude du plan en damier de la colonie trajane et reconstitution 3D des édifices publics.",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "Timgad — Thamugadi en latin — est fondée en l'an 100 par l'empereur Trajan pour les vétérans de la IIIe légion Auguste.",
                "Surnommée la « Pompéi africaine », elle illustre à la perfection la grille hippodamienne romaine appliquée à un terrain vierge.",
            ]),
            ("Histoire", [
                "# Histoire",
                "Apogée au IIe et IIIe siècles avec une population estimée à 15 000 habitants. Crise au IVe siècle liée à la querelle donatiste.",
                "Pillée par les Vandales puis détruite par les révoltes berbères (Ve-VIIe s.), elle est ensevelie par les sables et redécouverte en 1880.",
            ]),
            ("Description architecturale", [
                "# Description architecturale",
                "Plan carré de 355 m de côté, orienté est-ouest selon un cardo et un decumanus rigoureusement perpendiculaires.",
                "L'arc de Trajan, la bibliothèque (l'une des seules connues en Afrique romaine) et le théâtre de 4 000 places sont les pièces maîtresses.",
            ]),
            ("Conservation et menaces", [
                "# Conservation",
                "Site exposé à l'érosion éolienne et aux variations thermiques. Mission CNRPAH-INRAP en cours sur la stabilisation des mosaïques.",
            ]),
        ],
        "members": [
            ("hocine.mansouri@cnrpah.dz", "lead"),
            ("samira.cherif@univ-batna.dz", "contributor"),
            ("expert@patrimoine.dz", "reviewer"),
        ],
        "status": "in_progress",
        "discussions": [
            {
                "title": "Capacité réelle du théâtre antique",
                "type": "conflict", "status": "open",
                "messages": [
                    ("hocine.mansouri@cnrpah.dz", "Proposition: 3 500 places assises selon les calculs basés sur les gradins préservés.", True),
                    ("samira.cherif@univ-batna.dz", "Proposition: 4 000 places, conformément à la littérature classique (Boeswillwald 1905).", True),
                    ("expert@patrimoine.dz", "Les deux estimations doivent être présentées avec leurs sources respectives."),
                ],
                "votes": [
                    ("hocine.mansouri@cnrpah.dz", "approve"),
                    ("samira.cherif@univ-batna.dz", "reject"),
                    ("expert@patrimoine.dz", "abstain"),
                ],
            },
        ],
    },

    "Vallée du M'Zab — Ghardaïa": {
        "title": "Architecture vernaculaire du M'Zab",
        "description": "Documentation de la pentapole ibadite et de son architecture climatique exemplaire.",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "La vallée du M'Zab regroupe cinq cités fortifiées — Ghardaïa, Beni Isguen, Melika, Bounoura et El-Atteuf — fondées entre 1011 et 1350 par les Ibadites.",
                "Site UNESCO depuis 1982, elle est citée par Le Corbusier comme « la plus humaine des architectures ».",
            ]),
            ("Histoire", [
                "# Histoire",
                "Refuge pour la communauté ibadite après la chute du royaume rostémide de Tahert (909), la pentapole se développe selon un urbanisme défensif et religieux strict.",
                "Sous l'occupation française (1882-1962), le M'Zab conserve une large autonomie administrative et conserve ses coutumes.",
            ]),
            ("Description architecturale", [
                "# Description architecturale",
                "Chaque cité est organisée en cercles concentriques autour de la mosquée et de son minaret pyramidal.",
                "Maisons à patio, terrasses étagées et venelles couvertes assurent un confort thermique remarquable malgré 50 °C estivaux.",
                "La palmeraie d'été et son système d'irrigation par foggaras complètent l'écosystème oasien.",
            ]),
            ("Enjeux contemporains", [
                "# Enjeux",
                "Pression démographique forte, étalement urbain hors-les-murs et climatisation menacent l'équilibre traditionnel.",
            ]),
        ],
        "members": [
            ("karim.saadi@cnrpah.dz", "lead"),
            ("expert@patrimoine.dz", "contributor"),
            ("riad.hamdi@univ-oran.dz", "contributor"),
        ],
        "status": "in_progress",
        "discussions": [
            {
                "title": "Tracer l'extension de la palmeraie sur les cartes anciennes",
                "type": "general", "status": "open",
                "messages": [
                    ("karim.saadi@cnrpah.dz", "Les cartes IGN de 1958 montrent une palmeraie 30 % plus étendue qu'aujourd'hui."),
                ],
            },
        ],
    },

    "Qalâa des Béni Hammad": {
        "title": "Premier site UNESCO d'Algérie",
        "description": "Étude historico-archéologique de la première capitale hammadide.",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "Fondée en 1007 par Hammad ibn Buluggin, fils du fondateur d'Alger, la Qalâa devient capitale d'un état berbère puissant jusqu'en 1090.",
                "Premier site algérien classé UNESCO (1980), elle culmine à 1 000 m d'altitude dans les monts du Hodna.",
            ]),
            ("Histoire", [
                "# Histoire",
                "Capitale de la dynastie hammadide pendant un siècle, abandonnée au profit de Béjaïa après 1090 sous la pression des Hilaliens.",
                "Pillée et détruite par les Almohades en 1152, elle ne sera jamais réhabitée.",
            ]),
            ("Description architecturale", [
                "# Description architecturale",
                "Vestiges du Dar el-Bahr, du Qasr el-Manâr et de la grande mosquée à 13 nefs.",
                "Le minaret carré de 25 m, finement sculpté, témoigne du raffinement de l'art ziride-hammadide.",
            ]),
        ],
        "members": [
            ("amina.belhadj@univ-alger.dz", "lead"),
            ("hocine.mansouri@cnrpah.dz", "contributor"),
        ],
        "status": "published",
        "discussions": [],
    },

    "Mosquée Sidi Boumediene": {
        "title": "Complexe Sidi Boumediene à El-Eubbad",
        "description": "Documentation du complexe religieux mérinide attribué à Abou-l-Hassan en 1339.",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "Le complexe d'El-Eubbad englobe la mosquée, la médersa, la zaouïa et le mausolée de Sidi Boumediene Choaib (mort en 1198).",
                "Édifié en 1339 par le sultan mérinide Abou-l-Hassan, c'est un des chefs-d'œuvre de l'art hispano-mauresque.",
            ]),
            ("Architecture", [
                "# Architecture",
                "Portail monumental orné de zelliges et stuc, plafond en muqarnas devant le mihrab, minaret à coupole.",
                "Le mausolée présente un dôme à pendentifs orné de plâtre sculpté.",
            ]),
            ("Restauration récente", [
                "# Restauration",
                "Programme de restauration mené entre 2010 et 2015 sur les enduits du minaret et la coupole du mausolée.",
            ]),
        ],
        "members": [
            ("leila.bouzid@univ-tlemcen.dz", "lead"),
            ("amina.belhadj@univ-alger.dz", "contributor"),
            ("expert@patrimoine.dz", "reviewer"),
        ],
        "status": "in_progress",
        "discussions": [
            {
                "title": "Authenticité des stucs restaurés en 2014",
                "type": "conflict", "status": "resolved",
                "messages": [
                    ("leila.bouzid@univ-tlemcen.dz", "Les analyses chimiques confirment l'usage de matériaux traditionnels (plâtre + chaux + œuf)."),
                    ("amina.belhadj@univ-alger.dz", "OK, mais demander la publication du rapport ICOMOS de 2015."),
                ],
                "votes": [
                    ("leila.bouzid@univ-tlemcen.dz", "approve"),
                    ("amina.belhadj@univ-alger.dz", "approve"),
                ],
            },
        ],
    },

    "Mosquée Ketchaoua": {
        "title": "Restauration et histoire de la Mosquée Ketchaoua",
        "description": "Synthèse historique et documentation de la restauration turque de 2018.",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "Édifiée en 1612, la Mosquée Ketchaoua est le seul édifice religieux d'Alger transformé en cathédrale puis restitué au culte musulman.",
            ]),
            ("Histoire mouvementée", [
                "# Histoire",
                "Reconstruite en 1794 par le dey Hassan Pacha. Devenue cathédrale Saint-Philippe en 1845. Restituée à l'islam le 1er novembre 1962.",
                "Restaurée à l'identique entre 2014 et 2018 par la TIKA (Agence turque de coopération).",
            ]),
            ("Description", [
                "# Description architecturale",
                "Plan basilical à trois nefs, façade à double escalier monumental, deux minarets ottomans, coupole centrale à pendentifs.",
            ]),
        ],
        "members": [
            ("expert@patrimoine.dz", "lead"),
            ("amina.belhadj@univ-alger.dz", "contributor"),
        ],
        "status": "published",
        "discussions": [],
    },

    "Palais Ahmed Bey": {
        "title": "Palais Ahmed Bey de Constantine",
        "description": "Documentation du dernier palais beylical d'Algérie ottomane.",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "Construit entre 1825 et 1835 par Ahmed Bey, dernier bey ottoman de Constantine, juste avant la conquête française de la ville.",
            ]),
            ("Architecture", [
                "# Architecture",
                "Trois cours intérieures à arcades, fontaines en marbre, jardins en terrasse.",
                "Décor de fresques murales orientalistes mêlant scènes de pèlerinage à La Mecque et représentations de Constantinople.",
            ]),
            ("Sources documentaires", [
                "# Sources",
                "Mercier E., Histoire de Constantine (1903) ; Vatin J.-C., L'Algérie politique (1974) ; archives du musée des arts et traditions populaires.",
            ]),
        ],
        "members": [
            ("amina.belhadj@univ-alger.dz", "lead"),
            ("chercheur@patrimoine.dz", "contributor"),
        ],
        "status": "in_progress",
        "discussions": [],
    },

    "Mansourah": {
        "title": "Cité mérinide de Mansourah",
        "description": "Étude des vestiges de la cité-camp mérinide érigée lors du siège de Tlemcen (1303).",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "Mansourah — « la victorieuse » — est édifiée par le sultan mérinide Abou Yaacoub lors du long siège de Tlemcen (1299-1307).",
                "Cité éphémère mais monumentale, son minaret tronqué de 38 m reste l'icône de Tlemcen.",
            ]),
            ("Histoire", [
                "# Histoire",
                "Reconstruite en 1335 par Abou-l-Hassan, abandonnée définitivement en 1359 après la défaite des Mérinides.",
            ]),
            ("Vestiges", [
                "# Vestiges",
                "Murailles de 4 km, Grande Mosquée à 13 nefs (vestiges au sol uniquement), restes du palais sultanien.",
            ]),
        ],
        "members": [
            ("leila.bouzid@univ-tlemcen.dz", "lead"),
            ("hocine.mansouri@cnrpah.dz", "contributor"),
        ],
        "status": "draft",
        "discussions": [],
    },

    "Mausolée Royal de Maurétanie (Tombeau de la Chrétienne)": {
        "title": "Mausolée royal de Maurétanie",
        "description": "Étude monumentale du mausolée numido-romain de Sidi Rached.",
        "pages": [
            ("Présentation", [
                "# Présentation",
                "Tumulus monumental de 60 m de diamètre et 40 m de hauteur, attribué traditionnellement au roi Juba II et à son épouse Cléopâtre Séléné II.",
                "L'appellation populaire « Tombeau de la Chrétienne » dérive d'une lecture erronée de la croix figurant sur la fausse porte.",
            ]),
            ("Architecture", [
                "# Architecture",
                "Cylindre orné de 60 colonnes engagées d'ordre ionique, surmonté d'un cône à degrés.",
                "Quatre fausses portes orientées aux points cardinaux, dont une seule donne accès au couloir intérieur en spirale.",
            ]),
            ("Datation et identification", [
                "# Datation",
                "L'attribution à Juba II (mort en 23 ap. J.-C.) reste débattue : certains chercheurs proposent une datation antérieure (Ier siècle av. J.-C.) liée à Bocchus II.",
            ]),
        ],
        "members": [
            ("hocine.mansouri@cnrpah.dz", "lead"),
            ("samira.cherif@univ-batna.dz", "contributor"),
        ],
        "status": "in_progress",
        "discussions": [
            {
                "title": "Datation : Juba II ou Bocchus II ?",
                "type": "conflict", "status": "open",
                "messages": [
                    ("hocine.mansouri@cnrpah.dz", "Proposition: datation traditionnelle Juba II (Ier siècle ap. J.-C.) confirmée par les fouilles Christofle (1951).", True),
                    ("samira.cherif@univ-batna.dz", "Proposition: datation antérieure Bocchus II (Ier s. av. J.-C.) selon l'analyse stylistique des chapiteaux.", True),
                ],
                "votes": [
                    ("hocine.mansouri@cnrpah.dz", "approve"),
                    ("samira.cherif@univ-batna.dz", "reject"),
                ],
            },
        ],
    },
}


class Command(BaseCommand):
    help = "Seed 10 enriched projects (pages, members, discussions, votes)."

    @transaction.atomic
    def handle(self, *args, **options):
        admin = User.objects.filter(role=User.Role.ADMIN).first()
        if not admin:
            self.stderr.write(self.style.ERROR(
                "No admin user found. Run `seed_demo_users` first."
            ))
            return

        # Discipline lookup for color-coding
        disc_arch = Discipline.objects.filter(name_fr="Architecture").first()

        projects_created = 0
        for resource_name, blueprint in PROJECT_BLUEPRINTS.items():
            resource = HeritageResource.objects.filter(name_fr=resource_name).first()
            if not resource:
                self.stdout.write(self.style.WARNING(
                    f"Skipping '{resource_name}' — resource not found (run seed_heritage)."
                ))
                continue

            # Get the lead user (first member) as project owner if available
            lead_email = next((e for e, role in blueprint["members"] if role == "lead"), None)
            lead = User.objects.filter(email=lead_email).first() if lead_email else admin

            project, created = Project.objects.update_or_create(
                resource=resource,
                defaults={
                    "title": blueprint["title"],
                    "description": blueprint["description"],
                    "status": blueprint["status"],
                    "created_by": lead or admin,
                },
            )
            if created:
                projects_created += 1

            # Members
            for email, role in blueprint["members"]:
                user = User.objects.filter(email=email).first()
                if not user:
                    continue
                ProjectMember.objects.update_or_create(
                    project=project, user=user,
                    defaults={"project_role": role},
                )

            # Pages + initial PageVersion
            for position, (title, paragraphs) in enumerate(blueprint["pages"]):
                page, _ = Page.objects.update_or_create(
                    project=project, title=title,
                    defaults={"position": position},
                )
                if not page.versions.exists():
                    version = PageVersion.objects.create(
                        page=page,
                        version_number=1,
                        content_json=doc(*paragraphs),
                        change_summary="Version initiale (seed)",
                        author=lead or admin,
                        discipline=disc_arch,
                        status=PageVersion.Status.PUBLISHED,
                    )
                    page.current_version = version
                    page.save(update_fields=["current_version"])

            # Discussions
            for d in blueprint.get("discussions", []):
                opener_email = d["messages"][0][0] if d.get("messages") else admin.email
                opener = User.objects.filter(email=opener_email).first() or admin
                disc_status = (
                    Discussion.Status.RESOLVED if d.get("status") == "resolved"
                    else Discussion.Status.OPEN
                )
                disc_type = (
                    Discussion.Type.CONFLICT if d.get("type") == "conflict"
                    else Discussion.Type.GENERAL
                )
                discussion, _ = Discussion.objects.update_or_create(
                    project=project, title=d["title"],
                    defaults={
                        "type": disc_type,
                        "status": disc_status,
                        "opened_by": opener,
                    },
                )
                # Wipe and recreate messages for idempotency
                discussion.messages.all().delete()
                for entry in d.get("messages", []):
                    if len(entry) == 3:
                        email, body, is_proposal = entry
                    else:
                        email, body = entry
                        is_proposal = False
                    author = User.objects.filter(email=email).first() or admin
                    Message.objects.create(
                        discussion=discussion,
                        author=author, body=body,
                        is_proposal=is_proposal,
                    )
                # Votes
                discussion.votes.all().delete()
                for email, choice in d.get("votes", []):
                    voter = User.objects.filter(email=email).first()
                    if not voter:
                        continue
                    ConflictVote.objects.create(
                        discussion=discussion, voter=voter,
                        choice=choice,
                    )

            self.stdout.write(self.style.SUCCESS(
                f"  ✓ {project.title} ({len(blueprint['pages'])} pages, "
                f"{len(blueprint['members'])} members, "
                f"{len(blueprint.get('discussions', []))} discussions)"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Done — {projects_created} new projects, "
            f"{Project.objects.count()} total."
        ))
