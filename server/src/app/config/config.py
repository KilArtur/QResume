import os
from dataclasses import dataclass, fields, is_dataclass
from typing import Literal

import yaml


@dataclass
class GptConfig:
    url: str
    token: str
    mode: Literal["openai", "vllm"]
    model_matching: str
    model_recalculate: str


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
class RecalculateConfig:
    lower_limit: float
    upper_limit: float


@dataclass
class Config:
    profile: str
    server_port: int
    prometheus_port: int
    api_schema_path: str
    gpt_primary: GptConfig
    gpt_fallback: GptConfig
    logging: LoggingConfig
    recalculate: RecalculateConfig
    threshold_no_human: float
    no_human_model_type: str


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

        self.__load_if_exists("/etc/cyntai-server/config.yml")
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
                # Получаем значение для обычного поля
                fname = f"{outer_name}{field.name}"
                val = get_value_func(fname)
                if val is None:
                    msg = f"Field {fname} is not specified"
                    raise Exception(msg)
                kwargs[field.name] = val

        return cls(**kwargs)


CONFIG: Config = ConfigLoader().load_config(Config)
