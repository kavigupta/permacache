class CacheMissError(Exception):
    pass


class error_on_miss:
    """
    context manager that sets the _error_on_miss attribute of a cache to True,
    and then sets it back to False when the context is exited
    """

    def __init__(self, cache):
        self.cache = cache
        self.old = cache._error_on_miss

    def __enter__(self):
        self.cache._error_on_miss = True

    def __exit__(self, *args):
        self.cache._error_on_miss = self.old


class error_on_miss_global:
    """
    context manager that sets the error on miss attribute globally, and the
    resets it when the context is exited
    """

    error_on_miss = False

    def __enter__(self):
        self.old = error_on_miss_global.error_on_miss
        error_on_miss_global.error_on_miss = True

    def __exit__(self, *args):
        error_on_miss_global.error_on_miss = self.old
