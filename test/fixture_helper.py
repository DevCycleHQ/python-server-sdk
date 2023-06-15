import os
import json


def get_small_config() -> str:
    config_filename = os.path.join(os.path.dirname(__file__), 'fixture_small_config.json')
    with open(config_filename, 'r') as f:
        return f.read()


def get_small_config_json() -> dict:
    data = get_small_config()
    return json.loads(data)


def get_special_character_config() -> str:
    config_filename = os.path.join(os.path.dirname(__file__), 'fixture_small_config_special_characters.json')
    with open(config_filename, 'r') as f:
        return f.read()


def get_special_character_config_json() -> dict:
    data = get_special_character_config()
    return json.loads(data)


def large_config() -> str:
    config_filename = os.path.join(os.path.dirname(__file__), 'fixture_large_config.json')
    with open(config_filename, 'r') as f:
        return f.read()


def get_large_config_json() -> dict:
    data = large_config()
    return json.loads(data)
