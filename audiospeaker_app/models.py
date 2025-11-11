from django.db import models

class SpeechRequest(models.Model):
    """
    Модель для хранения информации о каждом запросе на синтез речи.
    Включает исходный текст, путь к аудиофайлу и использованные настройки.
    Без привязки к конкретному пользователю.
    """
    # Исходный текст, который был озвучен.
    text_content = models.TextField(
        verbose_name="Озвученный текст"
    )

    audio_file_path = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Путь к аудиофайлу"
    )

    voice_id = models.CharField(
        max_length=50,
        default='EXAVITQu4vr4xnSDxYa4', # Пример ID голоса Eleven Labs (Adam)
        verbose_name="ID голоса"
    )

    voice_settings = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name="Настройки голоса (стабильность, четкость и т.д.)"
    )

    model_id = models.CharField(
        max_length=100,
        default='eleven_multilingual_v2',
        verbose_name="ID модели синтеза"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время создания"
    )

    class Meta:
        verbose_name = "Запрос на озвучивание"
        verbose_name_plural = "Запросы на озвучивание"
        ordering = ['-created_at'] # Сортировка по убыванию даты создания (новые сверху)

    def __str__(self):

        return f"Запрос ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class RecognitionRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'В обработке'),
        ('COMPLETED', 'Завершено'),
        ('FAILED', 'Ошибка'),
    ]

    # Оригинальный аудиофайл, загруженный пользователем
    uploaded_audio_file = models.FileField(
        upload_to='uploads/',
        verbose_name="Загруженный аудиофайл"
    )

    # Распознанный текст (может быть пустым, пока идет обработка)
    recognized_text = models.TextField(
        verbose_name="Распознанный текст",
        blank=True,
        null=True
    )

    # Дата создания записи
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    # Статус выполнения запроса
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Статус"
    )

    # Поле для хранения сообщений об ошибках
    error_message = models.TextField(
        verbose_name="Сообщение об ошибке",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Запрос на распознавание"
        verbose_name_plural = "Запросы на распознавание"
        ordering = ['-created_at']

    def __str__(self):
        text_preview = (self.recognized_text or "...")[:50]
        return f"Распознавание от {self.created_at.strftime('%d.%m.%Y %H:%M')} - '{text_preview}'"