from typing import Union

__all__ = (
    'JSON',
    'YAML'
)

JSON = YAML = dict[str, Union[str, int, float, bool, None, list, dict]]
