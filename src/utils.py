import logging

from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import EmptyResponseException, ParserFindTagException


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        if response is None:
            raise EmptyResponseException(
                f'Вернулся пустой ответ при запросе на {url}'
            )
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def prepare_soup(response):
    return BeautifulSoup(response.text, features='lxml')


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def build_dir(base_dir, subdir):
    dir = base_dir / subdir
    dir.mkdir(exist_ok=True)
    return dir
