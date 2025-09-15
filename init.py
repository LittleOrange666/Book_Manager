import os
import re
import time

import docker
import requests


def extract_temp_password(logs):
    """Extract temporary password from container logs."""
    pattern = r"A temporary password is provided for this session: (\w+)"
    match = re.search(pattern, logs)
    if match:
        return match.group(1)
    return None

def change_qbittorrent_password(ip, port, username, temp_password, new_password):
    """Change qBittorrent Web UI password via HTTP requests."""
    session = requests.Session()
    login_url = f"http://{ip}:{port}/api/v2/auth/login"
    settings_url = f"http://{ip}:{port}/api/v2/app/setPreferences"

    # Login to Web UI
    login_data = {"username": username, "password": temp_password}
    response = session.post(login_url, data=login_data)
    if response.status_code != 200 or response.text != "Ok.":
        raise Exception(f"Login failed: {response.text}")

    # Change password
    new_settings = {
        "web_ui_username": username,
        "web_ui_password": new_password
    }
    # qBittorrent API requires JSON payload with preferences
    payload = {"json": '{"web_ui_username":"' + username + '","web_ui_password":"' + new_password + '"}'}
    response = session.post(settings_url, data=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to change password: {response.status_code} {response.text}")

    print("Password changed successfully.")
    session.get(f"http://{ip}:{port}/api/v2/auth/logout")

def create_temp_qbittorrent_container(new_password):
    """Create a temporary qBittorrent container, extract temp password, and change it."""
    # Initialize Docker client
    client = docker.from_env()

    # Container parameters
    container_name = "temp_qbittorrent"
    image = "lscr.io/linuxserver/qbittorrent:latest"
    volumes = {
        os.path.abspath("./data/config"): {
            "bind": "/config",
            "mode": "rw"
        }
    }
    environment = {
        "PUID": "1000",
        "PGID": "1000",
        "TZ": "Asia/Taipei",
        "WEBUI_PORT": "8080"
    }
    ports = {
        "8080/tcp": 8080,
        "6881/tcp": 6881,
        "6881/udp": 6881
    }

    try:
        # Ensure ./data/config directory exists with correct permissions
        config_dir = os.path.abspath("./data/config")
        os.makedirs(config_dir, exist_ok=True)
        os.chown(config_dir, 1000, 1000)  # Match PUID:PGID
        print(f"Ensured config directory: {config_dir}")

        # Check for existing container and remove if present
        try:
            existing_container = client.containers.get(container_name)
            existing_container.stop()
            existing_container.remove()
            print(f"Removed existing container: {container_name}")
        except docker.errors.NotFound:
            pass

        # Create and start temporary container
        print(f"Creating and starting temporary container: {container_name}")
        container = client.containers.run(
            image,
            name=container_name,
            volumes=volumes,
            environment=environment,
            ports=ports,
            detach=True
        )

        # Wait for container to initialize
        time.sleep(10)  # Increased wait time for stability

        # Extract temporary password from logs
        logs = container.logs().decode("utf-8")
        temp_password = extract_temp_password(logs)
        if not temp_password:
            raise Exception("Failed to extract temporary password from logs.")
        print(f"Extracted temporary password: {temp_password}")

        # Change password via Web UI
        change_qbittorrent_password("localhost", 8080, "admin", temp_password, new_password)

        # Verify configuration file
        config_file = os.path.join(config_dir, "qBittorrent", "qBittorrent.conf")
        if os.path.exists(config_file):
            print(f"Configuration file verified at: {config_file}")
            with open(config_file, "r") as f:
                config_content = f.read()
                if "WebUI\\Password_PBKDF2" in config_content:
                    print("Password hash successfully set in configuration.")
                else:
                    print("Warning: Password hash not found in configuration.")
        else:
            print("Error: Configuration file not found.")

    except Exception as e:
        print(f"Error: {e}")
        # print(container.logs().decode("utf-8"))
    finally:
        # Clean up
        try:
            container = client.containers.get(container_name)
            container.stop()
            container.remove()
            print("Cleaned up temporary container.")
        except docker.errors.NotFound:
            pass

if __name__ == "__main__":
    # Specify new password
    custom_password = "adminmeow"
    create_temp_qbittorrent_container(custom_password)