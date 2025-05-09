import os
import yaml
from dataclasses import dataclass, fields, is_dataclass
from typing import Literal



@dataclass
class MistralConfig:
    api_key_mistral: str
    model_mistral_chat: str
    model_mistral_ocr: str

@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    model: str

@dataclass
class LoggingConfigGraylog:
    enabled: bool
    host: str
    port: int
    udp: bool


@dataclass
class LoggingConfigConsole:
    enabled: bool


@dataclass
class LoggingConfig:
    console: LoggingConfigConsole
    graylog: LoggingConfigGraylog
    app_name: str
    root_level: str
    levels: dict[str, str]


@dataclass
class Config:
    mistral: MistralConfig
    llm: LLMConfig
    logging: LoggingConfig


class ConfigLoader:

    def __init__(self):
        self.configs = []

    def __load_if_exists(self, filename, required=False):
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                yy = yaml.safe_load(f)
                if yy:
                    self.configs.append(yy)
        else:
            if required:
                raise Exception(f"Configuration file {filename} does not exists. Check the working folder.")

    def load_config(self, cls=Config) -> Config:
        profile = os.environ.get('PROFILE', 'dev')

        self.__load_if_exists("./config-local.yml")
        self.__load_if_exists(f"./config-{profile}.yml")
        self.__load_if_exists("./config.yml", required=True)

        return self.__create_class_from_values(cls, self.__get_value, "")

    def __get_value_from_yaml(self, data: dict, key: str):
        keys = key.split('.')
        value = data
        for k in keys:
            value = value.get(k)
            if value is None:
                return None
        return value

    def __get_value(self, vname):
        env_name = vname.upper().replace('.', '_')
        if os.getenv(env_name):
            res = os.getenv(env_name)
            if res.isdigit():
                return int(res)
            else:
                return res

        for c in self.configs:
            v = self.__get_value_from_yaml(c, vname)
            if v is not None:
                return v

    def __create_class_from_values(self, cls, get_value_func, outer_name):
        kwargs = {}

        for field in fields(cls):
            if is_dataclass(field.type):
                kwargs[field.name] = self.__create_class_from_values(field.type, get_value_func,
                                                                     f"{outer_name}{field.name}.")
            else:
                fname = f"{outer_name}{field.name}"
                val = get_value_func(fname)
                if val is None:
                    msg = f"Field {fname} is not specified"
                    raise Exception(msg)
                kwargs[field.name] = val

        return cls(**kwargs)


CONFIG: Config = ConfigLoader().load_config(Config)
