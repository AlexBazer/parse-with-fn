from toolz.curried import curry, flip
from pyquery import PyQuery
__all__ = ['PyQuery', 'pq_text', 'pq_find', 'pq_parents', 'pq_prev', 'pq_eq', 'pq_attr']

pq_text = lambda q: PyQuery(q).text()
pq_find = curry(lambda selector, q: PyQuery(q).find(selector))
pq_parents = curry(lambda selector, q: PyQuery(q).parents(selector))
pq_prev = curry(lambda q: PyQuery(q).prev())
pq_eq = curry(lambda i, q: PyQuery(q).eq(i))
pq_attr = curry(lambda attr_name, q: PyQuery(q).attr(attr_name))
