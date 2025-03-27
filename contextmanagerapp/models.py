from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    date = models.DateTimeField()
    sport = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self):
        return self.title


class POSStats(models.Model):
    objects = None
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="pos_stats")
    pos_tag = models.CharField(max_length=255)  # Часть речи (NOUN, VERB и т.д.)
    count = models.PositiveIntegerField()  # Количество вхождений

    def __str__(self):
        return f"{self.article.title} - {self.pos_tag}: {self.count}"


class WordAnalysis(models.Model):
    objects = None
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="word_analysis")
    word = models.CharField(max_length=255)  # Оригинальная словоформа
    lemma = models.CharField(max_length=255)  # Лемма слова
    pos = models.CharField(max_length=255)  # Часть речи
    morphology = models.TextField()  # Морфологические признаки (в виде строки)
    count = models.PositiveIntegerField()  # Частота слова в тексте
    concordance = models.JSONField()  # Конкордансные списки (список предложений, где встречается слово)

    def __str__(self):
        return f"{self.word} ({self.pos}) - {self.article.title}"
