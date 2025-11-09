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