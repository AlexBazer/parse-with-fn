from toolz.curried import flip, curry
from operator import add as default_add
__all__ = ['str_split', 'str_startswith', 'str_strip', 'add']

str_split = flip(str.split)
str_startswith = flip(str.startswith)
str_strip = flip(str.strip)
add = curry(default_add)
