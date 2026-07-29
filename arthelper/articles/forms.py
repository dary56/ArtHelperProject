from django import forms
from django.conf import settings
from .models import Article, Metadata, ArticleAuthor, Reference
from core.models import User
from django_ckeditor_5.widgets import CKEditor5Widget


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['content_html']
        widgets = {
            'content_html': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='default'
            ),
        }


class MetadataForm(forms.ModelForm):
    class Meta:
        model = Metadata
        fields = ['journal', 'title_ru', 'title_en', 'udc', 'supervisor',
                  'annotation_ru', 'annotation_en', 'keywords_ru', 'keywords_en']
        widgets = {
            'journal': forms.Select(attrs={'class': 'form-select'}),
            'title_ru': forms.TextInput(attrs={'class': 'form-control'}),
            'title_en': forms.TextInput(attrs={'class': 'form-control'}),
            'udc': forms.TextInput(attrs={
                'class': 'form-control',
                'list': 'udc-list',
                'placeholder': 'Введите код или название...'
            }),
            'supervisor': forms.Select(attrs={'class': 'form-select'}),
            'annotation_ru': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'annotation_en': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'keywords_ru': forms.TextInput(attrs={'class': 'form-control'}),
            'keywords_en': forms.TextInput(attrs={'class': 'form-control'}),
        }


class StudentAuthorForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role='student'),
        label='Студент',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TeacherAuthorForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role='teacher'),
        label='Преподаватель',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ReferenceDOIForm(forms.Form):
    doi = forms.CharField(
        label='DOI',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '10.1234/example'
        })
    )
    # source_type убран — определяется автоматически по Crossref


class ReferenceManualForm(forms.Form):
    source_type = forms.ChoiceField(
        label='Тип источника',
        choices=[('print', 'Печатный'), ('electronic', 'Электронный ресурс')],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'manual-source-type'  # для JS
        })
    )
    authors = forms.CharField(
        label='Авторы',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control manual-field',
            'placeholder': 'Иванов И.И., Петрова А.А.'
        })
    )
    title = forms.CharField(
        label='Название',
        widget=forms.TextInput(attrs={
            'class': 'form-control manual-field',
            'placeholder': 'Название статьи или книги'
        })
    )
    year = forms.CharField(
        label='Год',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control manual-field',
            'placeholder': '2025'
        })
    )
    journal = forms.CharField(
        label='Журнал / Издательство',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control manual-field',
            'placeholder': 'Вестник КубГАУ / Издательство Юг'
        })
    )
    issue = forms.CharField(
        label='Номер выпуска',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control manual-field print-only',
            'placeholder': '№ 3'
        })
    )
    pages = forms.CharField(
        label='Страницы',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control manual-field print-only',
            'placeholder': '45-52'
        })
    )
    url = forms.CharField(
        label='URL',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control manual-field electronic-only',
            'placeholder': 'https://example.com/article'
        })
    )