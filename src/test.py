import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin

STATUS_COUNT = {
    'Accepted': 0,
    'Active': 0,
    'Deferred': 0,
    'Draft': 0,
    'Final': 0,
    'Provisional': 0,
    'Rejected': 0,
    'Superseded': 0,
    'Withdrawn': 0,
    'Total': 0
}

EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}


if __name__ == '__main__':
    session = requests_cache.CachedSession()
    response = session.get('https://peps.python.org/')
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    all_tables = soup.find_all(
        'table', attrs={'class': 'pep-zero-table docutils align-default'})
    for current_table in tqdm(all_tables):
        table_body = current_table.find('tbody')
        all_current_table_rows = table_body.find_all('tr')
        for current_row in all_current_table_rows:
            try:
                preview_status = current_row.find('abbr').text[1:]
            except AttributeError:
                print('что-то не так в превью')
            href = current_row.find(attrs={'class': 'pep reference internal'})['href']
            link = urljoin('https://peps.python.org/', href)
            response = session.get(link)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, features='lxml')
            main_dl = soup.find('dl')
            pre_status_string = main_dl.find(string='Status').parent
            status_string = pre_status_string.find_next_sibling().string
            if status_string not in EXPECTED_STATUS[preview_status]:
                print('Опа у нас тут несовпадающие статусы')
                continue
            
            
            STATUS_COUNT[status_string] += 1

    print(STATUS_COUNT)
            
            

            
    

