from django.db import models


class Document(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='uploads/', blank=True, null=True)
    language = models.CharField(max_length=10, choices=[('en', 'English'), ('ru', 'Russian')])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title or 'Document'} ({self.language})"


class TranslationPair(models.Model):
    source_doc = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='source_pairs')
    target_doc = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='target_pairs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source_doc.title} → {self.target_doc.title}"


class WordAnalysisEn(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='word_analysis_en')
    word = models.CharField(max_length=100)
    lemma = models.CharField(max_length=100)
    pos = models.CharField(max_length=50)  # POS tag (например, NOUN, VERB)
    morph = models.CharField(max_length=200, blank=True)  # морфологические признаки (Number, Tense и т.д.)
    frequency = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.word} ({self.lemma}) [EN]"


class WordAnalysisRu(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='word_analysis_ru')
    word = models.CharField(max_length=100)
    lemma = models.CharField(max_length=100)
    pos = models.CharField(max_length=50)  # часть речи: СУЩ, ГЛ, ПРИЛ, и т.д.
    morph = models.CharField(max_length=200, blank=True)  # род, число, падеж и пр.
    frequency = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.word} ({self.lemma}) [RU]"


class WordDictionary(models.Model):
    source_word = models.ForeignKey(WordAnalysisEn, on_delete=models.CASCADE, related_name='translations')
    target_word = models.ForeignKey(WordAnalysisRu, on_delete=models.CASCADE, related_name='sources')
    confidence = models.FloatField(default=1.0)  # уверенность в переводе (0–1)

    def __str__(self):
        return f"{self.source_word.word} → {self.target_word.word}"


class SyntaxTree(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='syntax_trees')
    sentence = models.TextField()
    tree_data = models.JSONField()  # структура зависимостей (узлы, типы связей)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Syntax tree for {self.document.title}"
