import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, MAIN_PEPS_URL
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    main_div = find_tag(
        BeautifulSoup(response.text, features='lxml'), 'section',
        attrs={'id': 'what-s-new-in-python'}
    )
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    sidebar = find_tag(
        BeautifulSoup(response.text, features='lxml'),
        'div',
        attrs={'class': 'sphinxsidebarwrapper'}
    )
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    table_tag = find_tag(
        BeautifulSoup(response.text, features='lxml'),
        'table',
        attrs={'class': 'docutils'}
    )
    pdf_a4_tag = find_tag(
        table_tag,
        'a',
        {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    archive_url = urljoin(downloads_url, pdf_a4_tag['href'])
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    statuses_counter = {
        'Accepted': 0,
        'Active': 0,
        'Deferred': 0,
        'Draft': 0,
        'Final': 0,
        'Provisional': 0,
        'Rejected': 0,
        'Superseded': 0,
        'Withdrawn': 0,
        'Any statuses': 0,
        'Total': 0
    }
    response = get_response(session, MAIN_PEPS_URL)
    if response is None:
        return
    all_tables = BeautifulSoup(response.text, features='lxml').find_all(
        'table',
        attrs={'class': 'pep-zero-table docutils align-default'}
    )
    for current_table in tqdm(all_tables):
        table_body = find_tag(current_table, 'tbody')
        table_rows = table_body.find_all('tr')
        for current_row in tqdm(table_rows):
            try:
                preview_status = current_row.find('abbr').text[1:]
            except AttributeError:
                preview_status = ''
                error_tag = current_row.find(
                    attrs={'class': 'pep reference internal'}
                )
                logging.exception(
                    f'Нет типа и статуса в таблице у PEP - {error_tag.text}'
                )
            pep_link = urljoin(
                MAIN_PEPS_URL,
                find_tag(
                    current_row,
                    'a',
                    attrs={'class': 'pep reference internal'}
                )['href']
            )
            response = get_response(session, pep_link)
            if response is None:
                return
            main_dl = find_tag(
                BeautifulSoup(response.text, features='lxml'),
                'dl'
            )
            pre_status_section = main_dl.find(string='Status').parent
            status = pre_status_section.find_next_sibling().string
            if status not in EXPECTED_STATUS[preview_status]:
                logging.info(
                    'Несовпадающие статусы:\n'
                    f'{pep_link}\n'
                    f'Статус в карточке: {status}\n'
                    f'Ожидаемые статусы: {EXPECTED_STATUS[preview_status]}'
                )
                statuses_counter['Any statuses'] += 1
                continue
            statuses_counter[status] += 1
    statuses_counter['Total'] = sum(statuses_counter.values())
    results = [('Статус', 'Количество')]
    results.extend(statuses_counter.items())
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    args = configure_argument_parser(MODE_TO_FUNCTION.keys()).parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
