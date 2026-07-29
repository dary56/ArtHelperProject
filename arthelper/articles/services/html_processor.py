import os
from bs4 import BeautifulSoup
from django.conf import settings


def process_content_for_export(article):
    html = article.content_html or ''
    if not html.strip():
        return ''

    soup = BeautifulSoup(html, 'html.parser')

    # === Рисунки: <figure> + <figcaption> (как было — работало лучше всего) ===
    img_counter = 1
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src.startswith('/media/'):
            abs_path = os.path.join(str(settings.MEDIA_ROOT), src.replace('/media/', ''))
            img['src'] = abs_path

        for attr in ['width', 'height']:
            if img.has_attr(attr):
                del img[attr]
        img['style'] = 'max-width:100%;height:auto;'

        caption_text = img.get('alt', '').strip() or 'Иллюстрация'

        figure = soup.new_tag('figure')
        figcaption = soup.new_tag('figcaption')
        figcaption.string = f'Рисунок {img_counter} – {caption_text}'

        img.replace_with(figure)
        figure.append(img)
        figure.append(figcaption)

        img_counter += 1

    # === Таблицы: подпись сверху, без bold ===
    table_counter = 1

    for figure in list(soup.find_all('figure', class_='table')):
        table = figure.find('table')
        if not table:
            figure.decompose()
            continue

        figcaption = figure.find('figcaption')
        if figcaption:
            caption_text = figcaption.get_text(strip=True)
            figcaption.decompose()
        else:
            caption_text = ''

        table['data-processed'] = '1'

        # Подпись без жирности, по центру
        caption_p = soup.new_tag('p', style='text-align:justify;text-indent:0;margin-bottom:5px;')
        if caption_text:
            caption_p.string = f'Таблица {table_counter} – {caption_text}'
        else:
            caption_p.string = f'Таблица {table_counter}'
        figure.insert_before(caption_p)

        figure.replace_with(table)
        table_counter += 1

    for table in soup.find_all('table'):
        if table.get('data-processed') == '1':
            continue
        table['data-processed'] = '1'

        caption_p = soup.new_tag('p', style='text-align:justify;text-indent:0;margin-bottom:5px;')
        caption_p.string = f'Таблица {table_counter}'
        table.insert_before(caption_p)
        table_counter += 1

    return str(soup)