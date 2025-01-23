

class no_cache_global:
    """
    context manager that sets the error on miss attribute globally, and the
    resets it when the context is exited
    """

    no_cache = False

    def __init__(self):
        self.old = None

    def __enter__(self):
        self.old = no_cache_global.no_cache
        no_cache_global.no_cache = True

    def __exit__(self, *args):
        assert self.old is not None
        no_cache_global.no_cache = self.old
