"""Проект HOMEWORK Статус-БОТ."""
import os
import sys
import logging
import time
from http import HTTPStatus

from dotenv import load_dotenv
import requests
import telegram

from exceptions import (
    NotForSend, WrongJSONDecode, EndPointIsNotAvailiable,
    RequestError, CurrentDateError
)

load_dotenv()

logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKENS_REQRIED = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600  # Секунды.
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> str:
    """Проверяем доступность переменных окружения."""
    tokens_str = ''
    tokens_misslist = [token for token in TOKENS_REQRIED
                       if not globals().get(token)]
    if tokens_misslist:
        tokens_str = ', '.join(tokens_misslist)
    return tokens_str


def send_message(bot: telegram.bot.Bot, message: str) -> None:
    """Отправляет сообщение в telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.TelegramError as error:
        logger.error(f'Ошибка отправки статуса в telegram: {error}')
    else:
        logger.debug('Статус отправлен в telegram')


def get_api_answer(current_timestamp: int) -> dict:
    """Отправляем запрос к API и получаем список домашних работ."""
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': current_timestamp},
    }
    try:
        response = requests.get(**params_request)
        if response.status_code != HTTPStatus.OK:
            raise EndPointIsNotAvailiable(
                f'Ответ от API не 200. '
                f'Код ответа: {response.status_code}. '
                f'Причина: {response.reason}. '
                f'Текст: {response.text}.'
            )
        return response.json()
    except requests.JSONDecodeError as error:
        message = f"Ошибка декодирования JSON: {error}"
        raise WrongJSONDecode(message, error)
    except requests.RequestException as error:
        message = f'Произошла ошибка при запросе к API: {error}'
        raise RequestError(message, error)


def check_response(response: dict) -> list:
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является dict')
    if 'homeworks' not in response:
        raise KeyError('Нет ключа homeworks в ответе API')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('homeworks не является list')
    if 'current_date' not in response:
        message = 'Нет ключа "current_date" в ответе API'
        raise CurrentDateError(message)
    current_date = response.get('current_date')
    if not isinstance(current_date, int):
        raise CurrentDateError('current_date не является int')
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает и проверяет статус работы."""
    if 'homework_name' not in homework:
        raise KeyError('Нет ключа homework_name в ответе от API')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус - {homework_status}')
    return ('Изменился статус проверки работы "{homework_name}". {verdict}'
            ).format(homework_name=homework_name,
                     verdict=HOMEWORK_VERDICTS[homework_status]
                     )


def main():
    """Основной цикл работы бота."""
    tokens_errors = check_tokens()
    if tokens_errors:
        logger.critical(
            f'Отсутствует токен: {tokens_errors}. '
            f'Бот остановлен!'
        )
        sys.exit(-1)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
            else:
                message = 'Нет новых статусов'
            if message != prev_message:
                send_message(bot, message)
                prev_message = message
            else:
                logger.info(message)
            current_timestamp = response['current_date']

        except NotForSend as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message, exc_info=True)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error(message, exc_info=True)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    current_working_directory = os.getcwd()
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s, %(levelname)s, Путь - %(pathname)s, '
            'Файл - %(filename)s, Функция - %(funcName)s, '
            'Номер строки - %(lineno)d, %(message)s'
        ),
        handlers=[logging.FileHandler(f'{current_working_directory}log.log',
                                      encoding='UTF-8'
                                      ),
                  logging.StreamHandler(sys.stdout)])
    main()
