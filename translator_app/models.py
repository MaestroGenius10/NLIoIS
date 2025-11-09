from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=255)
    language = models.CharField(max_length=10)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class TranslationPair(models.Model):
    source_doc = models.ForeignKey(Document, related_name='source_pair', on_delete=models.CASCADE)
    target_doc = models.ForeignKey(Document, related_name='target_pair', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class WordAnalysisEn(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    word = models.CharField(max_length=100)
    lemma = models.CharField(max_length=100)
    pos = models.CharField(max_length=10)
    frequency = models.PositiveIntegerField(default=1)
    def __str__(self): return f"{self.word} ({self.pos}) in {self.document.title}"

class WordAnalysisRu(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    word = models.CharField(max_length=100)
    lemma = models.CharField(max_length=100)
    pos = models.CharField(max_length=10)
    frequency = models.PositiveIntegerField(default=1)
    def __str__(self): return f"{self.word} ({self.pos}) in {self.document.title}"

class LemmaEn(models.Model):
    lemma = models.CharField(max_length=100, unique=True)
    pos = models.CharField(max_length=10, blank=True)
    def __str__(self): return self.lemma

class LemmaRu(models.Model):
    lemma = models.CharField(max_length=100, unique=True)
    pos = models.CharField(max_length=10, blank=True)
    def __str__(self): return self.lemma

class DictionaryPair(models.Model):
    source_lemma = models.ForeignKey(LemmaEn, on_delete=models.CASCADE)
    target_lemma = models.ForeignKey(LemmaRu, on_delete=models.CASCADE)
    translation_count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('source_lemma', 'target_lemma')

    def __str__(self):
        return f"{self.source_lemma.lemma} -> {self.target_lemma.lemma}"