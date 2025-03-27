from django import forms
from .models import WordAnalysis, Article


class ArticleForm(forms.Form):
    file = forms.FileField(label='Select a file')


class WordEditForm(forms.ModelForm):
    class Meta:
        model = WordAnalysis
        fields = ['word', 'lemma', 'pos', 'morphology', 'count', 'concordance']


class ArticleEditForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'author', 'date', 'sport', 'content']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'content': forms.Textarea(attrs={'rows': 20}),
        }
