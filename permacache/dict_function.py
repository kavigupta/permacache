import attr

from .utils import parallelize_arguments, bind_arguments

DEFAULT_FUNCTIONS = {None: lambda x: None}


class drop_if:
    def __init__(self, predicate, mapper=lambda x: x):
        self.predicate = predicate
        self.mapper = mapper


@attr.s
class parallel_output:
    values = attr.ib()


def drop_if_equal(value, mapper=lambda x: x):
    return drop_if(lambda x: x == value, mapper)


def dict_function(d, fn):
    def key(args, kwargs, *, parallel=()):
        arguments = bind_arguments(fn, args, kwargs)
        if not parallel:
            return bind(arguments)
        all_args = parallelize_arguments(arguments, parallel)
        return parallel_output([bind(v) for v in all_args])

    def bind(arguments):
        result = {}
        for k, v in arguments.items():
            if k in d:
                if isinstance(d[k], drop_if):
                    if d[k].predicate(v):
                        continue
                    v = d[k].mapper(v)
                elif callable(d[k]):
                    v = d[k](v)
                else:
                    v = DEFAULT_FUNCTIONS[d[k]](v)
            result[k] = v
        return result

    return key
