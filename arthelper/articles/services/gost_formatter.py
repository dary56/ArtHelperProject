from datetime import datetime

def format_gost(data, source_type='print'):
    """
    Форматирует библиографическую запись по ГОСТ Р 7.0.5-2008.
    source_type: 'print' или 'electronic'
    """
    authors = data.get('authors', '')
    title = data.get('title', '')
    year = data.get('year', '')
    journal = data.get('journal', '')
    publisher = data.get('publisher', '')
    volume = data.get('volume', '')
    issue = data.get('issue', '')
    page = data.get('page', '')
    doi = data.get('doi', '')
    url = data.get('url', '')
    
    if source_type == 'electronic':
        # ГОСТ Р 7.0.108-2022 — электронные ресурсы
        access_date = datetime.now().strftime('%d.%m.%Y')
        if journal:
            # Статья в электронном журнале
            return f"{authors} {title} [Электронный ресурс] / {authors} // {journal}. — {year}. — URL: {url} (дата обращения: {access_date})."
        else:
            # Книга/документ
            return f"{authors} {title} [Электронный ресурс] / {authors}. — {publisher}, {year}. — URL: {url} (дата обращения: {access_date})."
    else:
        # ГОСТ Р 7.0.5-2008 — печатные источники
        if journal:
            # Статья в журнале
            issue_str = f" — № {issue}" if issue else ""
            page_str = f" — С. {page}" if page else ""
            return f"{authors} {title} / {authors} // {journal}. — {year}{issue_str}{page_str}."
        else:
            # Монография
            return f"{authors} {title} / {authors}. — {publisher}, {year}."