"""
Re-embed and upsert all retrievable chunks for the chatbot.

Usage:
    python manage.py reindex_chatbot
"""
from django.core.management.base import BaseCommand

from apps.chatbot.services.indexer import reindex


class Command(BaseCommand):
    help = "Re-embed and upsert all knowledge chunks used by the chatbot."

    def handle(self, *args, **opts):
        self.stdout.write("Reindexing chatbot corpus...")
        result = reindex()
        self.stdout.write(self.style.SUCCESS(
            f"Done. Indexed {result['indexed']} chunks, deleted {result['deleted']} stale rows."
        ))
