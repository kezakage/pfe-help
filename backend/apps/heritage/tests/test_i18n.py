"""Smoke test for the FR/AR translation catalogues.

The catalogues live under ``backend/locale/{fr,ar}/LC_MESSAGES/`` and are
compiled via ``compilemessages`` (a build-time step). This test does not
exercise any view; it only verifies that activating each language returns
a non-English (i.e. translated) result for a representative model verbose
name. It guards against the catalogue being silently lost or compiled
empty in the container image.
"""
from django.utils.translation import activate, gettext as _


def test_fr_catalogue_translates_mosque():
    activate("fr")
    assert _("Mosque") == "Mosquée"


def test_ar_catalogue_translates_mosque():
    activate("ar")
    # Arabic for "Mosque"; we don't pin the exact letterform, only that the
    # result is not the English msgid (i.e. a translation is loaded).
    out = _("Mosque")
    assert out != "Mosque"
    assert any("\u0600" <= ch <= "\u06FF" for ch in out), out
