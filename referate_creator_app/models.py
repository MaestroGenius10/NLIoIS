from django.db import models


class Document(models.Model):
    title = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    source_file = models.FileField(upload_to='uploads/')
    text_content = models.TextField()  # Исходный текст документа
    processed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Keyword(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="keywords")
    term = models.CharField(max_length=100)
    weight = models.FloatField(null=True, blank=True)
    source = models.CharField(
        max_length=50,
        choices=[("ollama", "Ollama"), ("tfidf", "TF*IDF")],
        default="ollama"
    )

    def __str__(self):
        return f"{self.term} ({self.source})"


class Summary(models.Model):
    SUMMARY_TYPE_CHOICES = [
        ("classic", "Классический реферат"),
        ("keywords", "Реферат ключевых слов"),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="summaries")
    summary_type = models.CharField(max_length=20, choices=SUMMARY_TYPE_CHOICES)
    content = models.TextField()
    generation_method = models.CharField(
        max_length=50,
        choices=[("tfidf", "TF*IDF"), ("ollama", "Ollama")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_summary_type_display()} — {self.document.title}"


class Sentence(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="sentences")
    text = models.TextField()
    weight = models.FloatField(default=0.0)  # Вес TF*IDF
    order_in_text = models.IntegerField()  # Порядок появления
    selected_for_summary = models.BooleanField(default=False)  # вошло ли в реферат

    def __str__(self):
        return f"Sentence {self.order_in_text} (w={self.weight:.3f})"
