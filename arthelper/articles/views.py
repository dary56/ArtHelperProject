from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from datetime import datetime

from .models import Article, Metadata, ArticleAuthor, Reference
from .forms import ArticleForm, MetadataForm, StudentAuthorForm, TeacherAuthorForm, ReferenceDOIForm, ReferenceManualForm
from journals.models import Journal
from core.models import User

import subprocess
import os
from django.core.files.base import File
from docx2pdf import convert

import json
from django.http import JsonResponse
from django.conf import settings

from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from .services.nlp_service import generate_annotation, extract_keywords, translate_text
from docx import Document

UDC_TREE = [
    {
        'code': '00',
        'name': 'Наука в целом. Информация. Документация',
        'children': [
            {
                'code': '004',
                'name': 'Информационные технологии. Вычислительная техника',
                'children': [
                    {'code': '004.01', 'name': 'Документация'},
                    {'code': '004.02', 'name': 'Методы решения задач'},
                    {'code': '004.03', 'name': 'Типы и характеристики систем'},
                    {'code': '004.04', 'name': 'Ориентация процесса обработки данных'},
                    {'code': '004.05', 'name': 'Качество систем и программ'},
                    {'code': '004.07', 'name': 'Характеристики памяти'},
                    {'code': '004.08', 'name': 'Носители вводимых и выводимых данных'},
                    {'code': '004.2', 'name': 'Архитектура вычислительных машин'},
                    {'code': '004.3', 'name': 'Аппаратные средства. Техническое обеспечение'},
                    {'code': '004.4', 'name': 'Программные средства'},
                    {'code': '004.5', 'name': 'Человеко-машинное взаимодействие'},
                    {
                        'code': '004.6',
                        'name': 'Данные',
                        'children': [
                            {'code': '004.62', 'name': 'Манипулирование данными'},
                            {'code': '004.63', 'name': 'Файлы'},
                            {'code': '004.65', 'name': 'Cистемы управления базами данных (СУБД)'},
                            {'code': '004.67', 'name': 'Системы обработки численных данных'},
                        ]
                    },
                    {'code': '004.7', 'name': 'Связь компьютеров. Сети ЭВМ'},
                    {'code': '004.8', 'name': 'Искусственный интеллект'},
                    {'code': '004.9', 'name': 'Прикладные информационные технологии'},
                ]
            },
            {'code': '005', 'name': 'Управление предприятием'},
            {'code': '006', 'name': 'Стандартизация'},
            {'code': '007', 'name': 'Деятельность и организация'},
        ]
    },
    {'code': '1', 'name': 'Философия. Психология'},
    {'code': '2', 'name': 'Религия. Теология'},
    {
        'code': '3',
        'name': 'Общественные науки',
        'children': [
            {
                'code': '33',
                'name': 'Экономика. Народное хозяйство. Экономические науки',
                'children': [
                    {'code': '330', 'name': 'Экономические науки в целом. Политическая экономия'},
                    {'code': '331', 'name': 'Труд. Наука о труде. Экономика труда'},
                    {'code': '332', 'name': 'Региональная (территориальная) экономика'},
                    {'code': '334', 'name': 'Формы организаций и сотрудничества в экономике'},
                    {'code': '336', 'name': 'Финансы. Банковское дело. Деньги'},
                    {'code': '338', 'name': 'Экономическое положение. Экономическая политика'},
                    {'code': '339', 'name': 'Торговля. Международные экономические отношения'},
                ]
            },
            {'code': '34', 'name': 'Право. Юридические науки'},
            {'code': '35', 'name': 'Государственное административное управление. Военное дело'},
            {'code': '37', 'name': 'Народное образование. Воспитание. Обучение'},
        ]
    },
    {'code': '5', 'name': 'Математика. Естественные науки'},
    {'code': '6', 'name': 'Прикладные науки. Медицина. Техника'},
    {'code': '7', 'name': 'Искусство. Декоративно-прикладное искусство'},
    {'code': '8', 'name': 'Языкознание. Филология. Литература'},
    {'code': '9', 'name': 'География. Биография. История'},
]

@login_required
def article_create(request):
    journals = Journal.objects.filter(templates__isnull=False).distinct()
    
    if request.method == 'POST':
        journal_id = request.POST.get('journal')
        draft_file = request.FILES.get('draft')
        
        if not journal_id:
            messages.error(request, 'Выберите журнал!')
            return render(request, 'articles/article_create.html', {'journals': journals})
        
        journal = get_object_or_404(Journal, pk=journal_id)
        
        # Создаём пустую статью
        article = Article.objects.create(user=request.user, content_html='')
        
        # Создаём метаданные с выбранным журналом
        meta = Metadata.objects.create(article=article, journal=journal)
        
        # Если загружен черновик .docx — парсим
        if draft_file:
            try:
                doc = Document(draft_file)
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                
                if paragraphs:
                    # Первая строка — название статьи
                    meta.title_ru = paragraphs[0]
                    
                    # Остальное — текст статьи, преобразуем в HTML
                    if len(paragraphs) > 1:
                        html_parts = []
                        for p in paragraphs[1:]:
                            if p.strip():
                                html_parts.append(f'<p>{p.strip()}</p>')
                        article.content_html = '\n'.join(html_parts)
                        article.save()
                    
                    meta.save()
                    messages.success(request, 'Черновик загружен! Название и текст извлечены из файла.')
            except Exception as e:
                messages.warning(request, f'Не удалось распарсить файл: {str(e)}')
        
        # Автоматически добавляем текущего пользователя как первого автора
        ArticleAuthor.objects.create(article=article, user=request.user)
        
        messages.success(request, 'Статья создана! Теперь заполните остальные метаданные.')
        return redirect('article_edit', pk=article.pk)
    
    return render(request, 'articles/article_create.html', {'journals': journals})


@login_required
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk, user=request.user)
    meta = article.metadata

    if request.method == 'POST':
        form_type = request.POST.get('form_type', '')

        # === Добавление студента-автора ===
        if 'add_student_author' in request.POST:
            form = StudentAuthorForm(request.POST)
            if form.is_valid():
                user = form.cleaned_data['user']
                if not ArticleAuthor.objects.filter(article=article, user=user).exists():
                    ArticleAuthor.objects.create(article=article, user=user)
                    messages.success(request, f'Студент «{user.full_name}» добавлен!')
                else:
                    messages.warning(request, 'Этот автор уже есть в списке!')
            else:
                messages.error(request, 'Выберите студента из списка.')
            return redirect('article_edit', pk=article.pk)

        # === Добавление преподавателя-автора ===
        elif 'add_teacher_author' in request.POST:
            form = TeacherAuthorForm(request.POST)
            if form.is_valid():
                user = form.cleaned_data['user']
                if not ArticleAuthor.objects.filter(article=article, user=user).exists():
                    ArticleAuthor.objects.create(article=article, user=user)
                    messages.success(request, f'Преподаватель «{user.full_name}» добавлен!')
                else:
                    messages.warning(request, 'Этот автор уже есть в списке!')
            else:
                messages.error(request, 'Выберите преподавателя из списка.')
            return redirect('article_edit', pk=article.pk)

        # === Форма добавления источника ===
        elif 'add_reference' in request.POST:
            if 'doi_mode' in request.POST:
                doi_form = ReferenceDOIForm(request.POST)
                if doi_form.is_valid():
                    try:
                        from .services.crossref_service import fetch_by_doi
                        from .services.gost_formatter import format_gost
                        
                        data = fetch_by_doi(doi_form.cleaned_data['doi'])
                        source_type = data.pop('source_type')
                        gost = format_gost(data, source_type)
                        
                        Reference.objects.create(
                            article=article,
                            doi=data['doi'],
                            raw_data=data,
                            source_type=source_type,
                            gost_string=gost
                        )
                        messages.success(request, f'Источник добавлен! Тип: {"электронный" if source_type == "electronic" else "печатный"}')
                    except Exception as e:
                        messages.error(request, f'Ошибка DOI: {str(e)}')
                else:
                    messages.error(request, 'Неверный формат DOI')
                    
            else:
                manual_form = ReferenceManualForm(request.POST)
                if manual_form.is_valid():
                    from .services.gost_formatter import format_gost
                    
                    data = {
                        'authors': manual_form.cleaned_data['authors'],
                        'title': manual_form.cleaned_data['title'],
                        'year': manual_form.cleaned_data['year'],
                        'journal': manual_form.cleaned_data['journal'],
                        'issue': manual_form.cleaned_data['issue'],
                        'page': manual_form.cleaned_data['pages'],
                        'url': manual_form.cleaned_data['url'],
                    }
                    source_type = manual_form.cleaned_data['source_type']
                    gost = format_gost(data, source_type)
                    
                    Reference.objects.create(
                        article=article,
                        raw_data=data,
                        source_type=source_type,
                        gost_string=gost
                    )
                    messages.success(request, 'Источник добавлен!')
                else:
                    messages.error(request, 'Заполните обязательные поля')
            return redirect('article_edit', pk=article.pk)

        # === Основная форма статьи ===
        else:
            article_form = ArticleForm(request.POST, instance=article)
            meta_form = MetadataForm(request.POST, instance=meta)
            if article_form.is_valid() and meta_form.is_valid():
                article_form.save()
                meta_form.save()
                messages.success(request, 'Статья сохранена!')
                return redirect('dashboard')

    # GET-запрос
    article_form = ArticleForm(instance=article)
    meta_form = MetadataForm(instance=meta)
    meta_form.fields['supervisor'].queryset = User.objects.filter(role='teacher')

    return render(request, 'articles/article_form.html', {
        'article_form': article_form,
        'meta_form': meta_form,
        'student_author_form': StudentAuthorForm(),
        'teacher_author_form': TeacherAuthorForm(),
        'doi_form': ReferenceDOIForm(),
        'manual_form': ReferenceManualForm(),
        'article': article,
        'authors': article.authors.select_related('user').order_by('order_num'),
        'references': article.references.order_by('order_num'),
        'title': 'Редактировать статью',
        'udc_tree': UDC_TREE,
    })


@login_required
def author_delete(request, pk):
    author = get_object_or_404(ArticleAuthor, pk=pk)
    article_pk = author.article.pk
    if author.article.user == request.user:
        author.delete()
        messages.success(request, 'Автор удалён!')
    return redirect('article_edit', pk=article_pk)


@login_required
def reference_delete(request, pk):
    ref = get_object_or_404(Reference, pk=pk)
    article_pk = ref.article.pk
    if ref.article.user == request.user:
        ref.delete()
        messages.success(request, 'Источник удалён!')
    return redirect('article_edit', pk=article_pk)


@login_required
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk, user=request.user)
    article.delete()
    messages.success(request, 'Статья удалена!')
    return redirect('dashboard')


def docx_to_pdf(docx_path):
    output_dir = os.path.dirname(docx_path)
    subprocess.run([
        'soffice', '--headless', '--convert-to', 'pdf',
        '--outdir', output_dir, docx_path
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    base = os.path.splitext(os.path.basename(docx_path))[0]
    return os.path.join(output_dir, base + '.pdf')


@login_required
def export_docx(request, pk):
    article = get_object_or_404(Article, pk=pk, user=request.user)

    if not hasattr(article, 'metadata') or not article.metadata.journal:
        messages.error(request, 'У статьи не выбран журнал!')
        return redirect('dashboard')

    if not article.metadata.journal.get_active_template():
        messages.error(request, 'У журнала нет активного шаблона!')
        return redirect('dashboard')

    try:
        # Удаляем старый docx
        if article.file_docx:
            old_path = article.file_docx.path
            article.file_docx.delete(save=False)
            if os.path.exists(old_path):
                os.remove(old_path)

        from .services.exporter import export_article_docx
        docx_file = export_article_docx(article)
        filename = f'article_{article.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'
        article.file_docx.save(filename, docx_file, save=True)

        response = FileResponse(
            article.file_docx.open(),
            as_attachment=True,
            filename=filename
        )
        return response

    except Exception as e:
        messages.error(request, f'Ошибка экспорта: {str(e)}')
        return redirect('dashboard')


@login_required
def export_pdf(request, pk):
    article = get_object_or_404(Article, pk=pk, user=request.user)

    # Если нет docx — сначала генерируем
    if not article.file_docx or not os.path.exists(article.file_docx.path):
        try:
            # Удаляем старый docx если есть
            if article.file_docx:
                old_path = article.file_docx.path
                article.file_docx.delete(save=False)
                if os.path.exists(old_path):
                    os.remove(old_path)

            from .services.exporter import export_article_docx
            docx_file = export_article_docx(article)
            docx_filename = f'article_{article.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'
            article.file_docx.save(docx_filename, docx_file, save=True)
        except Exception as e:
            messages.error(request, f'Ошибка генерации .docx: {str(e)}')
            return redirect('dashboard')

    try:
        # Удаляем старый pdf
        if article.file_pdf:
            old_path = article.file_pdf.path
            article.file_pdf.delete(save=False)
            if os.path.exists(old_path):
                os.remove(old_path)

        # Пути для конвертации
        docx_path = article.file_docx.path
        docx_dir = os.path.dirname(docx_path)
        pdf_name = f'article_{article.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        pdf_path = os.path.join(docx_dir, pdf_name)

        # Конвертация через docx2pdf (использует установленный MS Word)
        convert(docx_path, pdf_path)

        # Сохраняем в модель
        with open(pdf_path, 'rb') as f:
            article.file_pdf.save(pdf_name, File(f), save=True)

        # Удаляем временный pdf-файл из файловой системы (он уже в media)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        # Отдаём пользователю
        response = FileResponse(
            article.file_pdf.open(),
            as_attachment=True,
            filename=pdf_name
        )
        return response

    except Exception as e:
        messages.error(request, f'Ошибка экспорта PDF: {str(e)}')
        return redirect('dashboard')
    

@login_required
def udc_search(request):
    """AJAX-поиск УДК по коду или названию"""
    query = request.GET.get('q', '').lower()
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)

    json_path = settings.BASE_DIR / 'static' / 'data' / 'udc.json'
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return JsonResponse([], safe=False)

    results = [
        item for item in data
        if query in item['code'].lower() or query in item['name'].lower()
    ]
    return JsonResponse(results[:10], safe=False)

@login_required
@require_POST
def generate_annotation_ajax(request, pk):
    article = get_object_or_404(Article, pk=pk, user=request.user)
    text = article.content_html or ""
    annotation = generate_annotation(strip_tags(text), sentences_count=3)
    return JsonResponse({'annotation': annotation})


@login_required
@require_POST
def generate_keywords_ajax(request, pk):
    article = get_object_or_404(Article, pk=pk, user=request.user)
    text = article.content_html or ""
    keywords = extract_keywords(strip_tags(text), max_keywords=10)
    return JsonResponse({'keywords': keywords})


@login_required
@require_POST
def translate_metadata_ajax(request, pk):
    article = get_object_or_404(Article, pk=pk, user=request.user)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    text = data.get('text', '')
    if not text:
        return JsonResponse({'translation': ''})

    translated = translate_text(text, source_lang='ru', target_lang='en')
    return JsonResponse({'translation': translated})