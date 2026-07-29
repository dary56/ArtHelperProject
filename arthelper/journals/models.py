from django.db import models
import os
from datetime import datetime
from django.db.models.signals import post_delete
from django.dispatch import receiver


def template_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    now = datetime.now()
    new_name = f"шаблон_{now.year}_{now.month:02d}_{now.day:02d}_{now.hour:02d}{now.minute:02d}{ext}"
    return os.path.join('templates', str(instance.journal_id), new_name)


class Journal(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название журнала')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_active_template(self):
        return self.templates.order_by('-uploaded_at').first()

    def __str__(self):
        return self.title


class JournalTemplate(models.Model):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='templates',
        verbose_name='Журнал'
    )
    file = models.FileField(
        upload_to=template_upload_path,
        verbose_name='Файл шаблона'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Загружен')

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Версия шаблона'
        verbose_name_plural = 'Версии шаблонов'

    @property
    def filename(self):
        return os.path.basename(self.file.name)
    
    def __str__(self):
        return f"{self.journal.title} — {self.uploaded_at.strftime('%d.%m.%Y %H:%M')}"


@receiver(post_delete, sender=JournalTemplate)
def delete_template_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)