import copy

from attr import attrs, attrib
# from orjson import dumps, loads, OPT_INDENT_2, OPT_UTC_Z, OPT_SORT_KEYS
from json import dumps, loads
from typings.files import JSON


@attrs(init=False, repr=True)
class JsonConfig:
    """
    Base class of all config objects.
    """
    path = attrib(type=str, init=True)

    @staticmethod
    def validate_field(field_name: str) -> bool:
        return not (field_name.startswith('__') or field_name == 'path')

    @classmethod
    def from_file(cls, path):
        with open(path, mode='rt', encoding='utf-8') as f:
            config_dict: JSON = loads(f.read())     # speed up json load by using orjson
        return cls.from_json(path, config_dict)

    @classmethod
    def from_json(cls, path: str, json: JSON) -> 'JsonConfig':
        return cls(path=path, **json)

    def __init__(self, path: str, **fields):
        self.path = path
        for key, value in fields:
            if self.validate_field(key):
                setattr(self, key, value)

    def to_json(self) -> JSON:
        return {key: value for key, value in self.__dict__.items() if not key.startswith('__') and key != 'path'}

    def save(self):
        # with open(self.path, mode='wb') as f:
            # f.write(dumps(self.to_json(), option=OPT_SORT_KEYS | OPT_INDENT_2 | OPT_UTC_Z))     # speed up json dump by using orjson
        with open(self.path, mode='wt') as f:
            f.write(dumps(self.to_json(), indent=2, ensure_ascii=False, sort_keys=True))
