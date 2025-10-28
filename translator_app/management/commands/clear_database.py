from django.core.management.base import BaseCommand
from django.db import transaction
from translator_app.models import Document, TranslationPair, WordAnalysisEn, WordAnalysisRu, WordDictionary, SyntaxTree


class Command(BaseCommand):
    """
    Django-команда для полной очистки всех таблиц, связанных с переводами.
    """
    help = ('Deletes all data from translation-related tables: '
            'Document, TranslationPair, WordAnalysis, WordDictionary, and SyntaxTree.')

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.stdout.write("Начинаю очистку базы данных...")

                # Собираем информацию о количестве записей перед удалением
                counts = {
                    "WordDictionary": WordDictionary.objects.count(),
                    "WordAnalysisEn": WordAnalysisEn.objects.count(),
                    "WordAnalysisRu": WordAnalysisRu.objects.count(),
                    "SyntaxTree": SyntaxTree.objects.count(),
                    "TranslationPair": TranslationPair.objects.count(),
                    "Document": Document.objects.count(),
                }

                # Благодаря `on_delete=models.CASCADE` в ваших моделях,
                # удаление всех объектов `Document` автоматически приведет
                # к удалению связанных записей во всех остальных таблицах.
                # Это самый чистый и надежный способ.
                Document.objects.all().delete()

                self.stdout.write("\nУдаленные записи:")
                for model_name, count in counts.items():
                    if count > 0:
                        self.stdout.write(f"- {model_name}: {count}")

                self.stdout.write(self.style.SUCCESS(
                    '\n✅ База данных успешно очищена.'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Произошла ошибка: {e}'))