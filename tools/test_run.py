import os
import time

from dotenv import load_dotenv
import subprocess

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
print(env_path)
load_dotenv(env_path)


def main():
    envs = {
        "SERVER_PORT": "6756",
        "WEBUI_HOST": "localhost",
        "WEBUI_PORT": "8082",
        "WEBUI_USER": "admin",
        "WEBUI_PASS": os.getenv("WEBUI_PASSWORD", "password"),
        "ADMIN_KEY": os.getenv("ADMIN_KEY", "admin_key"),
        "MYSQL_DB": "bookmanager",
        "MYSQL_USER": "bookmanageruser",
        "MYSQL_PASSWORD": os.getenv("DB_PASSWORD", "password"),
        "MYSQL_HOST": "localhost:3306",
        "BOOK_PATH": os.getenv("BOOK_PATH", "./books")
    }
    print(envs)
    os.system("docker compose down")
    os.system("docker compose -f docker-compose-test.yml up -d")
    time.sleep(10)
    subprocess.run(["python3", "main.py"], env={**os.environ, **envs})


if __name__ == "__main__":
    main()
