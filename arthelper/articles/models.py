from django.db import models
import os
from datetime import datetime
from django.conf import settings
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver


def article_docx_path(instance, filename):
    ext = '.docx'
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join('articles', 'docx', f'{instance.id}_{now}{ext}')


def article_pdf_path(instance, filename):
    ext = '.pdf'
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join('articles', 'pdf', f'{instance.id}_{now}{ext}')


class Article(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='Пользователь'
    )
    content_html = models.TextField(blank=True, verbose_name='HTML-содержимое')
    file_docx = models.FileField(
        upload_to=article_docx_path,
        blank=True, null=True,
        verbose_name='Файл .docx'
    )
    file_pdf = models.FileField(
        upload_to=article_pdf_path,
        blank=True, null=True,
        verbose_name='Файл .pdf'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if hasattr(self, 'metadata') and self.metadata.title_ru:
            return self.metadata.title_ru
        return f"Статья №{self.id}"


class Metadata(models.Model):
    article = models.OneToOneField(
        Article,
        on_delete=models.CASCADE,
        related_name='metadata'
    )
    journal = models.ForeignKey(
        'journals.Journal',
        on_delete=models.CASCADE,
        verbose_name='Журнал'
    )
    title_ru = models.CharField(max_length=500, blank=True, verbose_name='Название статьи на русском')
    title_en = models.CharField(max_length=500, blank=True, verbose_name='Название статьи на английском')
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'teacher'},
        related_name='supervised_articles',
        verbose_name='Научный руководитель'
    )
    udc = models.CharField(max_length=50, blank=True, verbose_name='УДК')
    annotation_ru = models.TextField(blank=True, verbose_name='Аннотация на русском')
    annotation_en = models.TextField(blank=True, verbose_name='Аннотация на английском')
    keywords_ru = models.CharField(max_length=500, blank=True, verbose_name='Ключевые слова на русском')
    keywords_en = models.CharField(max_length=500, blank=True, verbose_name='Ключевые слова на английском')


class ArticleAuthor(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='authors'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authored_articles',
        limit_choices_to={'role__in': ['student', 'teacher']}
    )
    order_num = models.PositiveIntegerField(default=0, verbose_name='Порядковый номер')

    class Meta:
        ordering = ['order_num']
        constraints = [
            models.UniqueConstraint(fields=['article', 'user'], name='unique_article_author')
        ]

    def save(self, *args, **kwargs):
        if self.order_num == 0:
            last = ArticleAuthor.objects.filter(article=self.article).aggregate(
                max_num=models.Max('order_num')
            )['max_num'] or 0
            self.order_num = last + 1
        super().save(*args, **kwargs)


@receiver(post_delete, sender=ArticleAuthor)
def recalc_author_order(sender, instance, **kwargs):
    authors = ArticleAuthor.objects.filter(article=instance.article).order_by('order_num')
    for index, author in enumerate(authors, start=1):
        if author.order_num != index:
            ArticleAuthor.objects.filter(pk=author.pk).update(order_num=index)


class Reference(models.Model):
    SOURCE_TYPES = [
        ('print', 'Печатный источник'),
        ('electronic', 'Электронный ресурс'),
    ]
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='references'
    )
    doi = models.CharField(max_length=100, blank=True, verbose_name='DOI')
    raw_data = models.JSONField(blank=True, null=True)
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_TYPES,
        default='print',
        verbose_name='Тип источника'
    )
    gost_string = models.TextField(blank=True, verbose_name='Библиографическая запись (ГОСТ)')
    order_num = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order_num']

    def save(self, *args, **kwargs):
        if self.order_num == 0:
            last = Reference.objects.filter(article=self.article).aggregate(
                max_num=models.Max('order_num')
            )['max_num'] or 0
            self.order_num = last + 1
        super().save(*args, **kwargs)


@receiver(post_delete, sender=Reference)
def recalc_reference_order(sender, instance, **kwargs):
    refs = Reference.objects.filter(article=instance.article).order_by('order_num')
    for index, ref in enumerate(refs, start=1):
        if ref.order_num != index:
            Reference.objects.filter(pk=ref.pk).update(order_num=index)


@receiver(pre_save, sender=Article)
def delete_old_article_files(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Article.objects.get(pk=instance.pk)
    except Article.DoesNotExist:
        return

    if old.file_docx and old.file_docx != instance.file_docx:
        if os.path.isfile(old.file_docx.path):
            os.remove(old.file_docx.path)
    if old.file_pdf and old.file_pdf != instance.file_pdf:
        if os.path.isfile(old.file_pdf.path):
            os.remove(old.file_pdf.path)


@receiver(post_delete, sender=Article)
def delete_article_files_on_delete(sender, instance, **kwargs):
    if instance.file_docx and os.path.isfile(instance.file_docx.path):
        os.remove(instance.file_docx.path)
    if instance.file_pdf and os.path.isfile(instance.file_pdf.path):
        os.remove(instance.file_pdf.path)