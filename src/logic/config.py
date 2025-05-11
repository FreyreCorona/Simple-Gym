import json
import os

CONFIG_FILE = "resources/config.json"

DEFAULT_CONFIG = {
    "theme": "light",
    "default_payment": 100,
    "language": "pt",
    "notification_settings": {
        "payment_expiration": True,  
        "notification_days": 5,
        "notification_method": "email",
        "due_msg":"",
        "overdue_msg":""
    },
    "bussines_name":"Academia",
    "pix_key":"pix"
}

def load_config():
    try:
        if not os.path.exists(CONFIG_FILE):
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG

        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)

    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG

def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
