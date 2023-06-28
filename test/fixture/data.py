import os
import json


def small_config() -> str:
    config_filename = os.path.join(
        os.path.dirname(__file__), "fixture_small_config.json"
    )
    with open(config_filename, "r") as f:
        return f.read()


def small_config_json() -> dict:
    data = small_config()
    return json.loads(data)


def special_character_config() -> str:
    config_filename = os.path.join(
        os.path.dirname(__file__), "fixture_small_config_special_characters.json"
    )
    with open(config_filename, "r") as f:
        return f.read()


def special_character_config_json() -> dict:
    data = special_character_config()
    return json.loads(data)


def large_config() -> str:
    config_filename = os.path.join(
        os.path.dirname(__file__), "fixture_large_config.json"
    )
    with open(config_filename, "r") as f:
        return f.read()


def large_config_json() -> dict:
    data = large_config()
    return json.loads(data)


def bucketed_config() -> str:
    config_filename = os.path.join(
        os.path.dirname(__file__), "fixture_bucketed_config.json"
    )
    with open(config_filename, "r") as f:
        return f.read()


def bucketed_config_minimal() -> str:
    config_filename = os.path.join(
        os.path.dirname(__file__), "fixture_bucketed_config_minimal.json"
    )
    with open(config_filename, "r") as f:
        return f.read()
