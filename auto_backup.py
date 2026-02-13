import os
import requests
import shutil
from datetime import datetime

# --- ТВОИ НАСТРОЙКИ ---
TOKEN = 'y0__xDtsLuGBRjblgMgia6AtBbv6Iebw9R6fQxJvVdCMa-jVJt5eg'
DB_PATH = 'db.sqlite3'  # Имя твоей базы данных
LOCAL_BACKUP_DIR = 'backups'
YANDEX_DIR = 'scooter_rental_backups'  # Папка, которая создастся на Яндекс.Диске


def upload_to_yandex(file_path, file_name):
    headers = {'Authorization': f'OAuth {TOKEN}'}

    # 1. Создаем папку на Яндекс.Диске (если её нет)
    requests.put(f'https://cloud-api.yandex.net/v1/disk/resources?path={YANDEX_DIR}', headers=headers)

    # 2. Запрашиваем ссылку для загрузки
    url = f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={YANDEX_DIR}/{file_name}&overwrite=true"
    res = requests.get(url, headers=headers)

    if res.status_code == 200:
        upload_url = res.json().get('href')
        # 3. Отправляем файл
        with open(file_path, 'rb') as f:
            upload_res = requests.put(upload_url, data=f)
            if upload_res.status_code in [201, 202]:
                print(f"[{datetime.now()}] Успех! Файл {file_name} теперь в облаке.")
            else:
                print(f"Ошибка при передаче данных: {upload_res.status_code}")
    else:
        print(f"Яндекс отказал в ссылке: {res.status_code}.")


def main():
    # Создаем локальную папку для копий, если её нет
    if not os.path.exists(LOCAL_BACKUP_DIR):
        os.makedirs(LOCAL_BACKUP_DIR)

    # Формируем имя файла с датой и временем
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backup_{timestamp}.sqlite3"
    backup_path = os.path.join(LOCAL_BACKUP_DIR, backup_name)

    try:
        # Копируем базу локально
        shutil.copy2(DB_PATH, backup_path)
        print(f"Локальная копия готова: {backup_name}")

        # Грузим в облако
        upload_to_yandex(backup_path, backup_name)
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == '__main__':
    main()