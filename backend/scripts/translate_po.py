"""
One-shot translator for the FR/AR django.po files.

We keep this in `scripts/` (not under any Django app) so it doesn't get
imported at runtime — it's only invoked manually after `makemessages`.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "locale"

TRANSLATIONS = {
    "The email must be set": ("L'adresse e-mail est obligatoire.", "البريد الإلكتروني مطلوب."),
    "Superuser must have is_staff=True.": ("Le super-utilisateur doit avoir is_staff=True.", "يجب أن يكون للمستخدم الخارق is_staff=True."),
    "Superuser must have is_superuser=True.": ("Le super-utilisateur doit avoir is_superuser=True.", "يجب أن يكون للمستخدم الخارق is_superuser=True."),
    "Administrator": ("Administrateur", "مسؤول"),
    "Validated expert": ("Expert validé", "خبير معتمد"),
    "Guest researcher": ("Chercheur invité", "باحث مدعو"),
    "Visitor": ("Visiteur", "زائر"),
    "Pending validation": ("En attente de validation", "في انتظار التحقق"),
    "Active": ("Actif", "نشط"),
    "Rejected": ("Rejeté", "مرفوض"),
    "email address": ("adresse e-mail", "البريد الإلكتروني"),
    "Heritage resource": ("Ressource patrimoniale", "مورد تراثي"),
    "Project": ("Projet", "مشروع"),
    "Page version": ("Version de page", "نسخة الصفحة"),
    "User": ("Utilisateur", "مستخدم"),
    "Assistant": ("Assistant", "المساعد"),
    "System": ("Système", "النظام"),
    "Open": ("Ouvert", "مفتوح"),
    "Resolved": ("Résolu", "محلول"),
    "Archived": ("Archivé", "مؤرشف"),
    "General": ("Général", "عام"),
    "Editorial conflict": ("Conflit éditorial", "نزاع تحريري"),
    "Review": ("Révision", "مراجعة"),
    "Approve": ("Approuver", "موافقة"),
    "Reject": ("Rejeter", "رفض"),
    "Abstain": ("S'abstenir", "امتناع"),
    "PDF": ("PDF", "PDF"),
    "CSV": ("CSV", "CSV"),
    "GeoJSON": ("GeoJSON", "GeoJSON"),
    "ZIP archive": ("Archive ZIP", "أرشيف ZIP"),
    "Pending": ("En attente", "قيد الانتظار"),
    "Processing": ("En cours de traitement", "قيد المعالجة"),
    "Done": ("Terminé", "منجز"),
    "Failed": ("Échec", "فشل"),
    "Skipped": ("Ignoré", "تم تخطيه"),
    "In progress": ("En cours", "قيد التنفيذ"),
    "Published": ("Publié", "منشور"),
    "Draft": ("Brouillon", "مسودة"),
    "Image": ("Image", "صورة"),
    "Video": ("Vidéo", "فيديو"),
    "Document": ("Document", "وثيقة"),
    "3D model": ("Modèle 3D", "نموذج ثلاثي الأبعاد"),
    "Prehistoric": ("Préhistorique", "ما قبل التاريخ"),
    "Numidian": ("Numide", "نوميدي"),
    "Roman": ("Romain", "روماني"),
    "Medieval": ("Médiéval", "العصور الوسطى"),
    "Ottoman": ("Ottoman", "عثماني"),
    "Colonial": ("Colonial", "استعماري"),
    "Contemporary": ("Contemporain", "معاصر"),
    "Mosque": ("Mosquée", "مسجد"),
    "Medersa": ("Médersa", "مدرسة"),
    "Palace": ("Palais", "قصر"),
    "Casbah / Medina": ("Casbah / Médina", "قصبة / مدينة"),
    "Traditional house": ("Maison traditionnelle", "منزل تقليدي"),
    "Fortification": ("Fortification", "تحصينات"),
    "Mausoleum": ("Mausolée", "ضريح"),
    "Church": ("Église", "كنيسة"),
    "Synagogue": ("Synagogue", "كنيس"),
    "Archaeological site": ("Site archéologique", "موقع أثري"),
    "Other": ("Autre", "أخرى"),
    "UNESCO World Heritage": ("Patrimoine mondial UNESCO", "تراث عالمي لليونسكو"),
    "National": ("National", "وطني"),
    "Regional": ("Régional", "إقليمي"),
    "Unclassified": ("Non classé", "غير مصنف"),
    "Project lead": ("Chef de projet", "قائد المشروع"),
    "Contributor": ("Contributeur", "مساهم"),
    "Reviewer": ("Réviseur", "مراجع"),
    "Project invitation": ("Invitation au projet", "دعوة إلى مشروع"),
    "New discussion message": ("Nouveau message de discussion", "رسالة نقاش جديدة"),
    "Annotation validated": ("Annotation validée", "تم التحقق من التعليق"),
    "Page version published": ("Version de page publiée", "تم نشر نسخة الصفحة"),
    "Export ready": ("Export prêt", "التصدير جاهز"),
    "Expert account validated": ("Compte expert validé", "تم اعتماد حساب الخبير"),
    "Expert account rejected": ("Compte expert rejeté", "تم رفض حساب الخبير"),
}

# Match "msgid "..." \n msgstr """ where msgstr is empty.
PAIR = re.compile(r'(msgid\s+"((?:[^"\\]|\\.)*)"\nmsgstr\s+)""', re.MULTILINE)


def patch_po(lang: str) -> None:
    po_path = ROOT / lang / "LC_MESSAGES" / "django.po"
    text = po_path.read_text(encoding="utf-8")
    idx = 0 if lang == "fr" else 1

    def replace(match):
        prefix, raw_id = match.group(1), match.group(2)
        msgid = raw_id.encode("utf-8").decode("unicode_escape")
        if msgid == "":
            return match.group(0)
        if msgid in TRANSLATIONS:
            tr = TRANSLATIONS[msgid][idx]
            esc = tr.replace("\\", "\\\\").replace('"', '\\"')
            return f'{prefix}"{esc}"'
        return match.group(0)

    new_text = PAIR.sub(replace, text)
    new_text = new_text.replace("#, fuzzy\n", "", 1)
    new_text = re.sub(r'"Language: \\n"', f'"Language: {lang}\\\\n"', new_text)
    po_path.write_text(new_text, encoding="utf-8")

    translated = sum(1 for m in re.finditer(r'msgstr "([^"]+)"', new_text)) - 1  # minus header
    total = sum(1 for m in re.finditer(r'msgid "([^"]+)"', new_text))
    print(f"[{lang}] {translated}/{total} translated -> {po_path}")


if __name__ == "__main__":
    for lang in ("fr", "ar"):
        patch_po(lang)
