import re
import inspect
from collections import OrderedDict


def deep_merge(* dicts):
    """ naive recursive of dicts and only dicts """
    def merge(d1, d2):
        r = dict(d1)
        for k, v in d2.items():
            if k in r:
                if isinstance(r[k], dict):
                    r[k] = merge(r[k], v)
                else:
                    r[k] = v
            else:
                r[k] = v
        return r

    res = {}
    for d in dicts:
        res = merge(res, d)

    return res

# Maybe look into
# https://docs.python.org/3/reference/datamodel.html?emulating-container-types=#emulating-container-types

class Config(dict):
    def __init__(self, defaults=None, config=None):
        self.defaults = defaults if isinstance(defaults, dict) else {}
        self.defaults = defaults or {}
        self.confset = OrderedDict(config if isinstance(config, dict) else {})

    def __getitem__(self, key):
        annotation = self.__transform_key__(key)
        # _, value = next(self.__match__(annotation), (None, {}))
        # keep going!
        value = dict(self.defaults)
        for _, v in self.__match__(annotation):
            value = deep_merge(value, v)
        return value
        # return deep_merge(dict(self.defaults), value)

    def __transform_key__(self, key):
        mod = inspect.getmodule(key)
        cls = key.__class__
        tag = key.tag
        return f'{mod.__name__}::{cls.__name__}::{tag}'

    def __match__(self, key):
        return filter(lambda k: re.match(k[0], key), self.confset.items())

    def __contains__(self, key):
        match = self.__match__(self.__transform_key__(key))
        return bool(next(match, None))

    def get(self, key, default=None):
        return self[key]

    def items(self):
        raise Exception()

    def keys(self):
        raise Exception()

    def __str__(self):
        return f"defaults: {self.defaults}\nconfset: {dict(self.confset)}"

def read_config(file):
  loc = {}
  exec(file.read(), {}, loc)
  return loc
