from util.fileutils import load_json

class Config:
    def __init__(self, config_dict):
        for key, value in config_dict.items():
            setattr(self, key, value)

def load_config(config_path):
    return Config(load_json(config_path))