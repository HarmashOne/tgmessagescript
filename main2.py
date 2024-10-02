import os
import asyncio
import pyfiglet
from telethon import TelegramClient, errors

API_FILE = 'api.txt'
DELAY_BETWEEN_RUNS = 15 * 60  # 15 минут в секундах


def show_welcome_message():
    ascii_art = pyfiglet.figlet_format("WorkScript")
    print(ascii_art)
    print("Добро пожаловать в WorkScript! Скрипт для автоматической отправки сообщений в Telegram.")
    print("=" * 80)


def get_api_data():
    if not os.path.exists(API_FILE):
        api_id = input("Введите ваш API ID: ").strip()
        api_hash = input("Введите ваш API Hash: ").strip()

        with open(API_FILE, 'w') as f:
            f.write(f'{api_id}\n{api_hash}')

    with open(API_FILE, 'r') as f:
        api_id, api_hash = f.read().splitlines()

    return api_id, api_hash


def get_valid_phone_number():
    phone = input("Введите ваш телефон (в формате +123456789): ").strip()
    return phone


async def get_last_saved_message(client):
    try:
        print("Получение последнего сообщения из избранных...")
        saved = await client.get_input_entity('me')
        messages = await client.get_messages(saved, limit=1)
        if messages:
            print("Последнее сообщение получено успешно.")
            return messages[0].message
        print("Сообщений в избранных не найдено.")
        return None
    except Exception as e:
        print(f"Произошла ошибка при получении последнего сообщения из избранного: {str(e)}")
        return None


def get_delay_time():
    while True:
        try:
            delay = int(input("Введите время задержки между отправкой сообщений (в секундах): ").strip())
            if delay >= 0:
                return delay
            else:
                print("Время задержки не может быть отрицательным. Попробуйте снова.")
        except ValueError:
            print("Некорректный ввод. Введите целое число.")


async def send_messages(client, last_message, delay_time):
    dialogs = await client.get_dialogs()
    target_channels = [dialog for dialog in dialogs if dialog.is_channel]

    for dialog in target_channels:
        dialog_name = "Неизвестный канал"
        try:
            dialog_name = dialog.title if hasattr(dialog, 'title') else str(dialog)

            print(f"Отправка сообщения в канал: {dialog_name}")
            await client.send_message(dialog, last_message)
            print(f'Сообщение отправлено в канал: {dialog_name}')

            await asyncio.sleep(delay_time)
        except errors.FloodWaitError as e:
            print(f'Слишком частые запросы. Пожалуйста, подождите {e.seconds} секунд.')
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f'Ошибка при отправке сообщения в {dialog_name}: {str(e)}')


async def start_messaging_cycle(client, delay_time):
    while True:
        last_message = await get_last_saved_message(client)
        if not last_message:
            print("Не удалось получить последнее сообщение из избранного.")
            return

        await send_messages(client, last_message, delay_time)

        print(f"Рассылка завершена. Ожидание {DELAY_BETWEEN_RUNS // 60} минут до следующего цикла...")
        await asyncio.sleep(DELAY_BETWEEN_RUNS)


async def send_messages_to_channels():
    phone = get_valid_phone_number()  # Запрашиваем и проверяем телефон
    api_id, api_hash = get_api_data()  # Получаем API-данные

    # Создаем клиента
    client = TelegramClient('session_name', api_id, api_hash)

    try:
        # Авторизуемся
        print("Начало авторизации...")
        await client.connect()  # Подключаем клиента

        # Проверяем авторизацию
        if not await client.is_user_authorized():
            await client.send_code_request(phone)  # Отправляем код на телефон
            code = input("Введите код, отправленный на ваш телефон: ")
            try:
                # Пытаемся войти с номером телефона и кодом
                await client.sign_in(phone, code=code)
            except Exception as e:  # Более общий блок для всех исключений
                print(f"Ошибка при входе с кодом: {str(e)}")
                if "Two-steps verification is enabled" in str(e):
                    password = input("Введите ваш пароль (двухфакторная аутентификация): ")
                    await client.sign_in(phone, code=code, password=password)  # Вход с паролем
                else:
                    print("Неизвестная ошибка, попробуйте еще раз.")
            except errors.FloodWaitError as e:
                # Обработка ошибки слишком частых запросов
                print(f'Слишком частые запросы. Пожалуйста, подождите {e.seconds} секунд.')

        print("Авторизация успешна!")

        # Здесь вы можете продолжить свою логику отправки сообщений
        # Например, запустите основной цикл рассылки
        delay_time = get_delay_time()
        await start_messaging_cycle(client, delay_time)

    except Exception as e:
        # Обработка ошибок на более высоком уровне
        print(f"Произошла ошибка в процессе работы программы: {str(e)}")
    finally:
        # Останавливаем клиент
        await client.disconnect()

# Показываем заставку
show_welcome_message()

# Запуск программы
asyncio.run(send_messages_to_channels())
