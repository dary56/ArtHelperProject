import requests

def fetch_by_doi(doi):
    url = f"https://api.crossref.org/works/{doi}"
    try:
        response = requests.get(url, timeout=10, headers={'Accept': 'application/json'})
        response.raise_for_status()
        data = response.json()['message']
        
        authors_list = []
        for author in data.get('author', []):
            family = author.get('family', '')
            given = author.get('given', '')
            initials = ' '.join([n[0] + '.' for n in given.split() if n])
            authors_list.append(f"{family} {initials}")
        authors = ', '.join(authors_list) if authors_list else ''
        
        # Автоопределение типа
        published_print = data.get('published-print')
        published_online = data.get('published-online')
        if published_print:
            year = published_print['date-parts'][0][0]
            source_type = 'print'
        elif published_online:
            year = published_online['date-parts'][0][0]
            source_type = 'electronic'
        else:
            year = ''
            source_type = 'print'
        
        return {
            'title': data.get('title', [''])[0],
            'authors': authors,
            'year': str(year),
            'journal': data.get('container-title', [''])[0],
            'publisher': data.get('publisher', ''),
            'volume': data.get('volume', ''),
            'issue': data.get('issue', ''),
            'page': data.get('page', ''),
            'doi': doi,
            'url': f"https://doi.org/{doi}",
            'source_type': source_type,
        }
    except Exception as e:
        raise ValueError(f"Ошибка получения данных по DOI: {str(e)}")