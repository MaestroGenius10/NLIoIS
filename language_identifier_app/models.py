from django.db import models


class Document(models.Model):
    """Модель документа, текст которого сохраняется напрямую в БД."""
    name = models.CharField(max_length=255, verbose_name="Название документа")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    text_content = models.TextField(verbose_name="Извлечённый текст")
    detected_language = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Определённый язык"
    )
    is_processed = models.BooleanField(default=False, verbose_name="Обработан ли документ")

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ['-upload_date']

    def __str__(self):
        return self.name


class LanguageProfile(models.Model):
    """Модель языкового профиля для обучения и сравнения."""
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('de', 'Немецкий'),
    ]

    language = models.CharField(
        max_length=2, choices=LANGUAGE_CHOICES, unique=True, verbose_name="Язык"
    )
    word_frequencies = models.JSONField(
        default=dict, verbose_name="Частоты слов (метод частотных слов)"
    )
    short_word_frequencies = models.JSONField(
        default=dict, verbose_name="Частоты коротких слов"
    )

    class Meta:
        verbose_name = "Языковой профиль"
        verbose_name_plural = "Языковые профили"

    def __str__(self):
        return self.get_language_display()


class AnalysisResult(models.Model):
    """Результаты анализа документа каждым методом."""
    METHOD_CHOICES = [
        ('freq', 'Метод частотных слов'),
        ('short', 'Метод коротких слов'),
        ('neural', 'Нейросетевой метод'),
    ]

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='results', verbose_name="Документ"
    )
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, verbose_name="Метод")
    detected_language = models.CharField(max_length=50, verbose_name="Определённый язык")
    accuracy_score = models.FloatField(
        blank=True, null=True, verbose_name="Уверенность (точность)"
    )
    processing_time = models.FloatField(
        blank=True, null=True, verbose_name="Время обработки (сек)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата анализа")

    class Meta:
        verbose_name = "Результат анализа"
        verbose_name_plural = "Результаты анализа"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.document.name} — {self.get_method_display()}"
