import pickle
import shelve


class swap_unpickler_context_manager:
    def __init__(self, unpickler_class):
        self._unpickler_class = unpickler_class
        self._previous_unpickler = None

    def __enter__(self):
        self._previous_unpickler = shelve.Unpickler
        shelve.Unpickler = self._unpickler_class

    def __exit__(self, type, value, traceback):
        if self._previous_unpickler is not None:
            shelve.Unpickler = self._previous_unpickler
            self._previous_unpickler = None
        else:
            shelve.Unpickler = pickle.Unpickler
