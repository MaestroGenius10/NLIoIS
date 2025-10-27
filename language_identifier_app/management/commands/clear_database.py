from django.core.management.base import BaseCommand
from language_identifier_app.models import Document, AnalysisResult


class Command(BaseCommand):
    help = 'Очищает все документы и результаты анализа из базы данных.'

    def handle(self, *args, **kwargs):
        # Удаляем все результаты анализа
        num_results = AnalysisResult.objects.count()
        AnalysisResult.objects.all().delete()

        # Удаляем все документы
        num_docs = Document.objects.count()
        Document.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f'База очищена: {num_docs} документов и {num_results} результатов анализа удалены.'
        ))
