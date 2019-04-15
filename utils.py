from toolz.curried import flip, curry, partial
from operator import add as default_add, ge as default_ge, le as default_le

__all__ = ['str_split', 'str_startswith', 'str_strip', 'add', 'str_find', 'ge', 'le', 'str_replace']

str_split = flip(str.split)
str_startswith = flip(str.startswith)
str_strip = flip(str.strip)
str_find = flip(str.find)
add = curry(default_add)
ge = curry(default_ge)
le = curry(default_le)

def str_replace(before, after):
    return lambda s: str.replace(s, before, after)

