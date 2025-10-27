from django.core.management.base import BaseCommand
from search_system_app.models import Document, SearchQuery, SearchResult

class Command(BaseCommand):
    help = "Очищает базу данных от всех документов и связанных с ними данных"

    def handle(self, *args, **options):
        # Удаляем все документы
        Document.objects.all().delete()
        # Удаляем историю поисковых запросов и результаты
        SearchResult.objects.all().delete()
        SearchQuery.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("База данных успешно очищена!"))
