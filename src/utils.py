from bs4 import BeautifulSoup
from requests import RequestException

from constants import DEFAULT_ENCODING
from exceptions import EmptyResponseException, ParserFindTagException

REQUEST_ERROR = 'Не удалось загрузить страницу {url}. Ошибка: {err}'
EMPTY_RESPONSE = 'Вернулся пустой ответ при запросе на {url}'
NO_TAG_MESSAGE = 'Не найден тег {tag} {attrs}'


def get_response(session, url, encoding=DEFAULT_ENCODING):
    try:
        response = session.get(url)
        response.encoding = encoding
        if response is None:
            raise EmptyResponseException(
                EMPTY_RESPONSE.format(url=url)
            )
        return response
    except RequestException as err:
        raise ConnectionError(
            REQUEST_ERROR.format(url=url, err=err)
        )


def prepare_soup(response):
    return BeautifulSoup(response.text, features='lxml')


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(
            NO_TAG_MESSAGE.format(tag=tag, attrs=attrs)
        )
    return searched_tag


def build_dir(base_dir, subdir):
    dir = base_dir / subdir
    dir.mkdir(exist_ok=True)
    return dir
