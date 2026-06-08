import json
import os
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

SALT_SIZE = 16        
KEY_SIZE = 32         
ITERATIONS = 100_000  

def generate_key(master_password: str, salt: bytes) -> bytes:
    """Превращает текстовый пароль в 32-байтный криптографический ключ."""
    return PBKDF2(master_password, salt, dkLen=KEY_SIZE, count=ITERATIONS)

def encrypt_data(data_dict: dict, master_password: str, filename: str):
    """Шифрует словарь Python и сохраняет в файл."""
    json_string = json.dumps(data_dict)
    plain_text_bytes = json_string.encode('utf-8')
    
    salt = os.urandom(SALT_SIZE)
    key = generate_key(master_password, salt)
    
    cipher = AES.new(key, AES.MODE_GCM)
    cipher_text_bytes, tag = cipher.encrypt_and_digest(plain_text_bytes)
    
    with open(filename, "wb") as f:
        f.write(salt)          
        f.write(cipher.nonce)  
        f.write(tag)           
        f.write(cipher_text_bytes) 

def decrypt_data(master_password: str, filename: str = "passwords.dat") -> dict:
    """Расшифровывает файл и возвращает словарь Python."""
    if not os.path.exists(filename):
        raise FileNotFoundError("Файл базы данных не найден!")
        
    with open(filename, "rb") as f:
        salt = f.read(16)
        nonce = f.read(16)
        tag = f.read(16)
        cipher_text_bytes = f.read()
        
    key = generate_key(master_password, salt)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    
    try:
        decrypted_bytes = cipher.decrypt_and_verify(cipher_text_bytes, tag)
        return json.loads(decrypted_bytes.decode('utf-8'))
    except ValueError:
        raise ValueError("Неверный Мастер-пароль или данные повреждены!") 
    

#==========ФУНКЦИИ РАБОТЫ С БЛОКИРОВКОЙ=============

def save_lock_time(until_timestamp):
    """Сохраняет на диск метку времени, до которой действует блокировка, не затирая другие данные."""
    # 1. Читаем то, что уже есть в файле, чтобы не сломать
    config = {}
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}

    # 2. Обновляем только нужный ключ
    config["lock_until"] = until_timestamp

    # 3. Записываем обновленный словарь обратно
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4) # indent=4 сделает JSON красивым и читаемым для человека


def get_lock_time():
    """Читает метку времени блокировки с диска. Если файла или ключа нет — возвращает 0."""
    if not os.path.exists("config.json"):
        return 0
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("lock_until", 0)
    except Exception:
        return 0


def save_failed_attempts(attempts):
    """Сохраняет количество неудачных попыток на диск, не затирая другие данные."""
    config = {}
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}

    # Обновляем только ключ попыток
    config["failed_attempts"] = attempts

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def get_failed_attempts():
    """Читает количество неудачных попыток с диска. Если файла нет — возвращает 0."""
    if not os.path.exists("config.json"):
        return 0
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("failed_attempts", 0)
    except Exception:
        return 0