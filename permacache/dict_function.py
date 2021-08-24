import inspect


DEFAULT_FUNCTIONS = {None: lambda x: None}


def dict_function(d, fn):
    signature = inspect.signature(fn)

    def key(*args, **kwargs):
        arguments = signature.bind(*args, **kwargs)
        arguments.apply_defaults()
        result = {}
        for k, v in arguments.arguments.items():
            if k in d:
                if callable(d[k]):
                    v = d[k](v)
                else:
                    v = DEFAULT_FUNCTIONS[d[k]](v)
            result[k] = v
        return result

    return key
