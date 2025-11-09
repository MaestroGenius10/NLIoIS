<<<<<<< HEAD
# translator_app/management/commands/cleardata.py

from django.core.management.base import BaseCommand
from django.db import transaction
from translator_app.models import (
    Document, TranslationPair,
    WordAnalysisEn, WordAnalysisRu,
    LemmaEn, LemmaRu, DictionaryPair
)


class Command(BaseCommand):
    # Описание команды, которое будет отображаться при вызове --help
    help = 'Deletes all data from the translator app models to start fresh.'

    def add_arguments(self, parser):
        # Добавляем опциональный аргумент --no-input для автоматического подтверждения
        parser.add_argument(
            '--no-input',
            '--noinput',
            action='store_true',
            dest='no_input',
            help='Do not prompt for confirmation before deleting data.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Список всех моделей, которые мы хотим очистить

        MODELS_TO_CLEAR = [
            # Сначала удаляем модели, которые ссылаются на другие (зависимые)
            DictionaryPair,
            WordAnalysisEn,
            WordAnalysisRu,
            TranslationPair,
            # Затем удаляем "родительские" модели
            LemmaEn,
            LemmaRu,
            Document,
        ]

        self.stdout.write(self.style.HTTP_INFO("\nStarting database cleanup..."))

        for model in MODELS_TO_CLEAR:
            model_name = model.__name__
            try:
                # Получаем количество объектов перед удалением
                count, _ = model.objects.all().delete()
                if count > 0:
                    self.stdout.write(self.style.SUCCESS(f"Successfully deleted {count} objects from {model_name}."))
                else:
                    self.stdout.write(f"No objects to delete from {model_name}.")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An error occurred while clearing {model_name}: {e}"))
                # Если произошла ошибка, прерываем транзакцию
                raise e

        self.stdout.write(self.style.SUCCESS("\n✅ Database cleanup complete! All specified tables are now empty."))
=======
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
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
