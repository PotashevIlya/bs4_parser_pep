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
from utils import build_dir, find_tag, prepare_soup

WHERE_IS_ARCHIVE_MESSAGE = 'Архив загружен. Путь: {path}'
START_PARSING_MESSAGE = 'Парсер запущен!'
STOP_PARSING_MESSAGE = 'Парсер завершил работу!'
CLI_ARGS_MESSAGE = 'Аргументы командной строки: {args}'
NO_PREVIEW_MESSAGE = 'Нет превью в таблице у PEP - {peps}'
NON_MATCHING_STATUSES_MESSAGE = (
    'Несовпадающие статусы:\n'
    '{}\n'
    'Статус в карточке: {}\n'
    'Ожидаемые статусы: {}'
)
ERROR_MESSAGE = 'Сбой в работе программы. Ошибка: {err}'


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    all_a_tags = prepare_soup(session, whats_new_url).select(
        '#what-s-new-in-python div.toctree-wrapper li.toctree-l1 > a.reference'
    )
    all_a_tags.pop()
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for tag in tqdm(all_a_tags):
        version_link = urljoin(whats_new_url, tag['href'])
        soup = prepare_soup(session, version_link)
        results.append(
            (
                version_link,
                find_tag(soup, 'h1').text,
                find_tag(soup, 'dl').text.replace('\n', ' ')
            )
        )
    return results


def latest_versions(session):
    sidebar = find_tag(
        prepare_soup(session, MAIN_DOC_URL),
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
    soup = prepare_soup(session, DOWNLOAD_URL)
    archive_url = urljoin(
        DOWNLOAD_URL,
        soup.select_one('table.docutils td > [href*="pdf-a4.zip"]')['href']
    )
    dir = build_dir(BASE_DIR, DOWNLOADS_DIR_NAME)
    archive_path = dir / archive_url.split('/')[-1]
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(WHERE_IS_ARCHIVE_MESSAGE.format(path=archive_path))


def pep(session):
    statuses_counter = {}
    peps_with_no_preview = []
    non_matching_statuses = []
    all_tables = prepare_soup(session, MAIN_PEPS_URL).find_all(
        'table',
        attrs={'class': 'pep-zero-table docutils align-default'}
    )
    for current_table in tqdm(all_tables):
        table_body = find_tag(current_table, 'tbody')
        table_rows = table_body.find_all('tr')
        for current_row in table_rows:
            try:
                preview_status = current_row.find('abbr').text[1:]
            except AttributeError:
                preview_status = ''
                peps_with_no_preview.append(
                    current_row.find(
                        attrs={'class': 'pep reference internal'}
                    ).text
                )
            pep_link = urljoin(
                MAIN_PEPS_URL,
                find_tag(
                    current_row,
                    'a',
                    attrs={'class': 'pep reference internal'}
                )['href']
            )
            main_dl = find_tag(
                prepare_soup(session, pep_link),
                'dl'
            )
            pre_status_section = main_dl.find(string='Status').parent
            status = pre_status_section.find_next_sibling().string
            if status not in statuses_counter:
                statuses_counter.setdefault(status, 0)
            statuses_counter[status] += 1
            if status not in EXPECTED_STATUS[preview_status]:
                non_matching_statuses.append(
                    (pep_link, status, EXPECTED_STATUS[preview_status])
                )
    logging.info(
        NO_PREVIEW_MESSAGE.format(peps=peps_with_no_preview)
    )
    for details in non_matching_statuses:
        logging.info(
            NON_MATCHING_STATUSES_MESSAGE.format(*details)
        )
    return [
        ('Статус', 'Количество'),
        *statuses_counter.items(),
        ('Всего', sum(statuses_counter.values()))
    ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info(START_PARSING_MESSAGE)
    args = configure_argument_parser(MODE_TO_FUNCTION.keys()).parse_args()
    logging.info(CLI_ARGS_MESSAGE.format(args=args))
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    try:
        results = MODE_TO_FUNCTION[parser_mode](session)
    except Exception as err:
        logging.error(
            ERROR_MESSAGE.format(err=err)
        )
    if results is not None:
        control_output(results, args)
    logging.info(STOP_PARSING_MESSAGE)


if __name__ == '__main__':
    main()
