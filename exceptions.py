"""Исключения для проекта HOMEWORK Статус-БОТ."""


class NotForSend(Exception):
    """Исключение не для пересылки в telegram."""

    pass


class WrongJSONDecode(Exception):
    """Неправильный формат JSON ответа."""

    pass


class EndPointIsNotAvailiable(Exception):
    """Обработка исключения при недоступности ENDPOINT API."""

    pass


class RequestError(Exception):
    """Обработка исключения при ошибке ответа от АПИ."""

    pass
