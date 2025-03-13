from django import forms
from .models import Collocation


class CollocationForm(forms.ModelForm):
    class Meta:
        model = Collocation
        fields = ['word1', 'part_of_speech1', 'word2', 'part_of_speech2', 'collocation', 'collocation_type']
        labels = {
            'word1': 'Word 1',
            'part_of_speech1': 'Part of Speech 1',
            'word2': 'Word 2',
            'part_of_speech2': 'Part of Speech 2',
            'collocation': 'Collocation',
            'collocation_type': 'Collocation Type',
        }
        widgets = {
            'word1': forms.TextInput(attrs={'class': 'form-control'}),
            'part_of_speech1': forms.TextInput(attrs={'class': 'form-control'}),
            'word2': forms.TextInput(attrs={'class': 'form-control'}),
            'part_of_speech2': forms.TextInput(attrs={'class': 'form-control'}),
            'collocation': forms.TextInput(attrs={'class': 'form-control'}),
            'collocation_type': forms.TextInput(attrs={'class': 'form-control'}),
        }
