import os
import yaml
import configparser


class ToDict:

    @classmethod
    def to_dict(cls):
        return cls.data

    @classmethod
    def set_data(cls, data):
        cls.data = data


class ConfigManager:

    @classmethod
    def __register_attribute(cls, cur_cls, data: dict = None):
        if data is None:
            data = dict()
        for k, v in data.items():
            if isinstance(v, dict):
                class _(ToDict):
                    pass

                _.set_data(v)
                cls.__register_attribute(_, v)
                setattr(cur_cls, k, _)
            else:
                setattr(cur_cls, k, v)
        # cls = cur_cls if cls is cur_cls else ...

    @classmethod
    def read_yaml(cls, yaml_file: str):
        # Load YAML into Python dictionary
        with open(yaml_file, 'r') as file:
            yaml_dict = yaml.safe_load(file)
            cls.__override_with_env_variables(yaml_dict)
            cls.__register_attribute(cur_cls=cls, data=yaml_dict)

    @classmethod
    def read_ini(cls, ini_file: str):
        config = configparser.ConfigParser()
        config.read(ini_file)
        cls.__override_with_env_variables(config._sections)
        cls.__register_attribute(cur_cls=cls, data=config._sections)

    @staticmethod
    def convert_type(value, original_type):
        """Convert the value to the original type."""
        try:
            if original_type is bool:
                return value.lower() in {"true", "1", "t", "y", "yes", "True", "T"}
            elif original_type is list:
                return [v.strip() for v in value.split(',')]
            else:
                return original_type(value)
        except ValueError:
            return value

    @classmethod
    def __override_with_env_variables(cls, config, prefix=''):
        """Recursively override configuration with environment variables if they exist."""
        if isinstance(config, dict):
            for key, value in config.items():
                env_key = f"{prefix}{key}".upper()
                if isinstance(value, dict):
                    cls.__override_with_env_variables(value, prefix=env_key + '_')
                else:
                    env_value = os.environ.get(env_key)
                    if env_value is not None:
                        config[key] = cls.convert_type(env_value, type(value))
        return config


# ConfigManager.read_yaml("/config/config.yaml")
