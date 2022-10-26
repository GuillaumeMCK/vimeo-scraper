from os import path
import sys
from configparser import ConfigParser

ABS_DIRECTORY = path.dirname(path.realpath(__file__))

CONFIG_FILE_DIR = path.join(ABS_DIRECTORY, "../config.ini")

"""
Permet de créer le fichier de configuration ou de le reset
"""
def config_file_checker(reset = False) -> None:
    
    if not path.exists(CONFIG_FILE_DIR) or reset:
        config = ConfigParser()
        config.add_section("Settings")
        config["Settings"] = {
            "dir"                 : path.join(ABS_DIRECTORY, "MANGAS"),
            "chrome_directory"    : path.join(ABS_DIRECTORY, "../bin/.chromium/chrome.exe"),
            "threads_count"       : 2,
        }
        with open(CONFIG_FILE_DIR, mode='w', encoding="utf-8") as config_file:
            config.write(config_file)

        print("Config file was written")
        
"""
Fonction pour retourner une information du fichier de configuration
"""
def get_config(key: str) -> str:
    config_file_checker()
    config = ConfigParser()
    config.read(CONFIG_FILE_DIR)
    value = config['Settings'][key]
    return value

"""
Fonction pour definir une information du fichier de configuration
"""
def set_config(key: str, value: str) -> None:
    config = ConfigParser()
    config.read(CONFIG_FILE_DIR)
    config['Settings'][key] = value
    with open(CONFIG_FILE_DIR, mode='w', encoding="utf-8") as config_file:
            config.write(config_file)