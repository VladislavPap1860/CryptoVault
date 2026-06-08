import requests

def upload_to_cloud(file_path):
    """
    Безопассно отправляет зашифрованный файл бэкапа в облако, доступное в РФ.
    """
    try:
        # Читаем наш зашифрованный файл
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Используем сервис paste.c-net.org
        # Отправляем файл обычной POST-командой
        response = requests.post(
            "https://paste.c-net.org/",  
            data=file_data, 
            timeout=10
        )
        
        if response.status_code == 200:
            # Сервер возвращает прямую текстовую ссылку на сохраненный файл
            return response.text.strip()
        else:
            print(f"[ОБЛАКО] Ошибка сервера: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ОБЛАКО] Ошибка соединения: {e}")
        return None


def download_from_cloud(url, file_path):
    """
    Скачивает зашифрованные байты из облака и сохраняет в локальный файл.
    """
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"[ОБЛАКО] Не удалось скачать, код: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ОБЛАКО] Ошибка при скачивании: {e}")
        return False