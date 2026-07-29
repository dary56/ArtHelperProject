import re
from .html_processor import process_content_for_export

def build_article_html(article):
    meta = article.metadata

    empty_line = '<p style="margin: 0; padding: 0;">&nbsp;</p>'

    supervisor_html = ''
    if meta.supervisor:
        sup = meta.supervisor
        parts = [sup.full_name]
        if sup.degree:
            parts.append(sup.degree)
        # Связка должность + кафедра
        if sup.position and sup.department:
            parts.append(f"{sup.position} кафедры {sup.department}")
        elif sup.position:
            parts.append(sup.position)
        elif sup.department:
            parts.append(f"кафедра {sup.department}")
        line = ', '.join(parts)
        supervisor_html = f'<p style="text-align: center; text-indent: 0; margin: 0; padding: 0;"><strong>{line},</strong></p>'

    # Авторы — построчно, запятая в конце строки с данными (или после ФИО если нет данных)
    authors = article.authors.select_related('user').order_by('order_num')
    total = authors.count()
    authors_html = ''
    for idx, a in enumerate(authors, start=1):
        user = a.user
        is_last = (idx == total)

        # Собираем данные автора
        data_parts = []
        if user.role == 'student':
            if user.course:
                data_parts.append(f'студент {user.course}-го курса')
            if user.faculty:
                data_parts.append(f'факультета {user.faculty}')
        elif user.role == 'teacher':
            if user.degree:
                data_parts.append(user.degree)
            # Связка должность + кафедра
            if user.position and user.department:
                data_parts.append(f"{user.position} кафедры {user.department}")
            elif user.position:
                data_parts.append(user.position)
            elif user.department:
                data_parts.append(f"кафедра {user.department}")

        # ФИО + данные + запятая в конце (всё в одном <p>)
        comma = '' if is_last else ','
        if user.role == 'teacher':
            data_str = ', '.join(data_parts)
            authors_html += f'<p style="text-align: center; text-indent: 0; margin: 0; padding: 0;"><strong>{user.full_name}</strong><br>{data_str}{comma}</p>'
        else: 
            data_str = ' '.join(data_parts)
            authors_html += f'<p style="text-align: center; text-indent: 0; margin: 0; padding: 0;"><strong>{user.full_name}</strong><br>{data_str}{comma}</p>'
        
    # УДК
    udk_html = f'<p style="text-align: left; text-indent: 0; margin: 0;"><strong>УДК {meta.udc}</strong></p>' if meta.udc else ''

    # Названия
    title_ru_html = f'<h1 style="text-align: center; text-indent: 0; margin: 0;">{meta.title_ru.upper()}</h1>' if meta.title_ru else ''
    title_en_html = f'<h1 style="text-align: center; text-indent: 0; margin: 0;">{meta.title_en.upper()}</h1>' if meta.title_en else ''

    # Аннотация и ключевые слова
    annotation_ru = f'<p style="text-indent: 0;"><strong>Аннотация:</strong> {meta.annotation_ru}</p>' if meta.annotation_ru else ''
    annotation_en = f'<p style="text-indent: 0;"><strong>Abstract:</strong> {meta.annotation_en}</p>' if meta.annotation_en else ''
    keywords_ru = f'<p style="text-indent: 0;"><strong>Ключевые слова:</strong> {meta.keywords_ru}</p>' if meta.keywords_ru else ''
    keywords_en = f'<p style="text-indent: 0;"><strong>Keywords:</strong> {meta.keywords_en}</p>' if meta.keywords_en else ''

    # Основной текст
    content = process_content_for_export(article)
    if '<p>' not in content and '<div>' not in content:
        paragraphs = re.split(r'\n\s*\n', content.strip())
        content = '\n'.join(
            f'<p>{p.strip().replace(chr(10), " ")}</p>'
            for p in paragraphs if p.strip()
        )

    # Литература
    refs = article.references.order_by('order_num')
    references_html = ''
    if refs.exists():
        references_html = '<h2>Список литературы</h2>\n'
        for ref in refs:
            if ref.gost_string:
                references_html += f'<p>{ref.order_num}. {ref.gost_string}</p>\n'
            elif ref.raw_data:
                title = ref.raw_data.get('title', ref.doi)
                references_html += f'<p>{ref.order_num}. {title}</p>\n'
            else:
                references_html += f'<p>{ref.order_num}. {ref.doi}</p>\n'

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
</head>
<body>
{udk_html}
{empty_line}
{title_ru_html}
{title_en_html}
{empty_line}
{supervisor_html}
{authors_html}
{empty_line}
{annotation_ru}
{annotation_en}
{keywords_ru}
{keywords_en}
{empty_line}
{content}
{references_html}
</body>
</html>"""
    return html