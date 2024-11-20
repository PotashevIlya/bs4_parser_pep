class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""


class EmptyResponseException(Exception):
    """Вызывается, когда response пуст."""
