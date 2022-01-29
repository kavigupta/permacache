import inspect


def parallelize_arguments(arguments, parallel_keys, indices=None):
    parallel_args = [arguments[k] for k in parallel_keys]
    lengths = {len(arg) for arg in parallel_args}
    if len(lengths) != 1:
        raise ValueError("Incompatible lengths: " + ", ".join(str(x) for x in lengths))
    if indices is not None:
        parallel_args = [[x[i] for i in indices] for x in parallel_args]
    parallel_args = [dict(zip(parallel_keys, values)) for values in zip(*parallel_args)]
    all_args = [
        {k: pa[k] if k in pa else arguments[k] for k in arguments}
        for pa in parallel_args
    ]

    return all_args


def bind_arguments(fn, args, kwargs):
    signature = inspect.signature(fn)
    arguments = signature.bind(*args, **kwargs)
    arguments.apply_defaults()
    arguments = arguments.arguments
    return arguments
