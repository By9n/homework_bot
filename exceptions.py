"""Исключения для проекта HOMEWORK Статус-БОТ."""


class WrongResponseCode(Exception):
    """Неверный ответ API."""

    pass


class NotForSend(Exception):
    """Исключение не для пересылки в telegram."""

    pass


class EmptyResponseFromAPI(NotForSend):
    """Пустой ответ API."""

    pass


class WrongJSONDecode(Exception):
    """Неправильный формат JSON ответа."""

    pass


class MissingEnvVar(Exception):
    """Не найден токен в окружении."""

    pass


class EndPointIsNotAvailiable(Exception):
    """Обработка исключения при недоступности ENDPOINT API."""

    pass


class RequestError(Exception):
    """Обработка исключения при ошибке ответа от АПИ."""

    pass
