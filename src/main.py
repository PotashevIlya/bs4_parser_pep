import logging
import re
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    BASE_DIR, DOWNLOADS_DIR_NAME, EXPECTED_STATUS,
    DOWNLOAD_URL, MAIN_DOC_URL, MAIN_PEPS_URL
)
from outputs import control_output
from utils import build_dir, get_response, find_tag, prepare_soup


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    sections_by_python = prepare_soup(response).select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1'
    )
    sections_by_python.pop()
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])
        response = get_response(session, version_link)
        soup = prepare_soup(response)
        results.append(
            (
                version_link,
                find_tag(soup, 'h1').text,
                find_tag(soup, 'dl').text.replace('\n', ' ')
            )
        )
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    sidebar = find_tag(
        prepare_soup(response),
        'div',
        attrs={'class': 'sphinxsidebarwrapper'}
    )
    ul_tag = sidebar.find('ul')
    a_tags = ul_tag.find_all('a')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (a_tag['href'], version, status)
        )
    return results


def download(session):
    response = get_response(session, DOWNLOAD_URL)
    table_tag = find_tag(
        prepare_soup(response),
        'table',
        attrs={'class': 'docutils'}
    )
    pdf_a4_tag = find_tag(
        table_tag,
        'a',
        {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    archive_url = urljoin(DOWNLOAD_URL, pdf_a4_tag['href'])
    dir = build_dir(BASE_DIR, DOWNLOADS_DIR_NAME)
    archive_path = dir / archive_url.split('/')[-1]
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
    all_tables = prepare_soup(response).find_all(
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
            main_dl = find_tag(
                prepare_soup(response),
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
