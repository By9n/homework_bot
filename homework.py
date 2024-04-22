import os
import sys
import logging
import time
from http import HTTPStatus

from dotenv import load_dotenv
import requests
import telegram

from exceptions import (EmptyResponseFromAPI, NotForSend, TelegramError,
                        WrongResponseCode)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = '71321:AAFI5DizOvZNxTLiQH_5fYLGnO2uvxJ3uQM'# os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600  # Секунды.
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """Проверка, что все токены доступны из окружения."""
    logging.info('Проверка наличия всех токенов')
    return all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID])

    
def send_message(bot: telegram.bot.Bot, message: str) -> None:
    """Отправляет сообщение в telegram."""
    try:
        logging.info('Начало отправки статуса в telegram')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.Unauthorized as error:
        logging.info('Начало555555555555555туса в telegram')
        raise TelegramError(f'Ошибка отправки статуса в telegram: {error}')
    else:
        logging.debug('Статус отправлен в telegram')


def get_api_answer(current_timestamp: int) -> dict:
    """Отправляем запрос к API и получаем список домашних работ."""
    timestamp = current_timestamp or int(time.time())
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    message = ('Начало запроса к API. Запрос: {url}, {headers}, {params}.'
               ).format(**params_request)
    logging.info(message)
    try:
        response = requests.get(**params_request)
        if response.status_code != HTTPStatus.OK:
            raise WrongResponseCode(
                f'Ответ API не возвращает 200. '
                f'Код ответа: {response.status_code}. '
                f'Причина: {response.reason}. '
                f'Текст: {response.text}.'
            )
        return response.json()
    except Exception as error:
        message = ('API не возвращает 200. Запрос: {url}, {headers}, {params}.'
                   ).format(**params_request)
        raise WrongResponseCode(message, error)



def check_response(response: dict) -> list:
    """Проверяет ответ API на корректность.
    Если ответ API соответствует ожиданиям,
    то функция должна вернуть список домашних работ (он может быть и пустым),
    доступный в ответе API по ключу 'homeworks'
    """
    logging.info('Проверка ответа API на корректность')
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является dict')
    if 'homeworks' not in response or 'current_date' not in response:
        raise EmptyResponseFromAPI('Нет ключа homeworks в ответе API')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('homeworks не является list')
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В случае успеха, функция возвращает подготовленную для отправки
    в Telegram строку.
    """
    logging.info('Проводим проверки и извлекаем статус работы')
    if 'homework_name' not in homework:
        raise KeyError('Нет ключа homework_name в ответе API')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы - {homework_status}')
    return ('Изменился статус проверки работы "{homework_name}". {verdict}'
            ).format(homework_name=homework_name,
                     verdict=HOMEWORK_VERDICTS[homework_status]
                     )

def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Отсутствует токен. Бот остановлен!'
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    start_message = 'Бот начал работу'
    send_message(bot, start_message)
    logging.info(start_message)
    prev_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get(
                'current_date', int(time.time())
            )
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
            else:
                message = 'Нет новых статусов'
            if message != prev_message:
                send_message(bot, message)
                prev_msg = message
            else:
                logging.info(message)

        except NotForSend as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            if message != prev_message:
                send_message(bot, message)
                prev_message = message

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
    level=logging.INFO,
    format=(
        '%(asctime)s, %(levelname)s, Путь - %(pathname)s, '
        'Файл - %(filename)s, Функция - %(funcName)s, '
        'Номер строки - %(lineno)d, %(message)s'
    ),
    handlers=[logging.FileHandler('log.txt', encoding='UTF-8'),
                logging.StreamHandler(sys.stdout)])
    main()
