from django.db import models


class Document(models.Model):
    """
    Хранит тексты (веб-страницы, статьи и т.п.), по которым осуществляется поиск.
    """
    title = models.CharField(max_length=300)
    url = models.URLField(unique=True)
    text = models.TextField()
    tokens = models.JSONField(null=True, blank=True, help_text="Список лемм документа")
    length = models.PositiveIntegerField(default=0, help_text="Количество токенов в документе")
    date_added = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=10, default='ru')
    domain = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.title[:70]}..." if len(self.title) > 70 else self.title


class SearchQuery(models.Model):
    """
    История пользовательских поисковых запросов.
    Сохраняется:
    - исходный текст запроса,
    - нормализованный текст (леммы),
    - основная лемма запроса,
    - список синонимов,
    - была ли успешная выдача,
    - дата создания.
    """
    query_text = models.TextField()
    normalized_text = models.TextField()
    main_lemma = models.CharField(max_length=100, blank=True, null=True, help_text="Главная лемма запроса")
    synonyms = models.JSONField(blank=True, null=True, help_text="Список синонимов запроса")
    has_results = models.BooleanField(default=False, help_text="Были ли результаты поиска")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.query_text} ({self.created_at:%Y-%m-%d %H:%M})"


class SearchResult(models.Model):
    """
    Результаты поиска для конкретного запроса.
    Сохраняет документы, релевантность и позицию в выдаче.
    """
    query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE, related_name='results')
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    rank = models.FloatField(help_text="Релевантность документа (BM25 score)")
    snippet = models.TextField(blank=True)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"#{self.position} {self.document.title[:50]} (rank={self.rank:.3f})"
