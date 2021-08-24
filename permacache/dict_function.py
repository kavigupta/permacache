import inspect


DEFAULT_FUNCTIONS = {None: lambda x: None}


class drop_if:
    def __init__(self, predicate, mapper=lambda x: x):
        self.predicate = predicate
        self.mapper = mapper


def drop_if_equal(value, mapper=lambda x: x):
    return drop_if(lambda x: x == value, mapper)


def dict_function(d, fn):
    signature = inspect.signature(fn)

    def key(*args, **kwargs):
        arguments = signature.bind(*args, **kwargs)
        arguments.apply_defaults()
        result = {}
        for k, v in arguments.arguments.items():
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
