import json
import hashlib
from types import SimpleNamespace


class TensorEncoder(json.JSONEncoder):
    fast_bytes = False

    def default(self, obj):
        original = obj
        if hasattr(obj, "__attrs_attrs__"):
            typename = type(obj).__name__
            obj = {a.name: getattr(obj, a.name) for a in obj.__attrs_attrs__}
            obj[".attr.__name__"] = typename
        if isinstance(obj, SimpleNamespace):
            obj = obj.__dict__
            obj[".builtin.__name__"] = "types.SimpleNamespace"
        obj = best_effort_to_bytes(obj)
        if isinstance(obj, bytes):
            if self.fast_bytes:
                obj = hashlib.sha256(obj).hexdigest()
            else:
                obj = str(obj)
        if isinstance(obj, range):
            obj = {".type": "range", "representation": str(obj)}
        if self.isinstance_str(obj, "Module"):
            obj = {
                ".type": "Module",
                "hash": dict(
                    other_dict={
                        k: v for k, v in obj.__dict__.items() if not k.startswith("_")
                    },
                    state_dict=obj.state_dict(),
                ),
            }
        if obj is original:
            return super().default(obj)
        return obj

    def isinstance_str(self, obj, str_type):
        try:
            return any(x.__name__ == str_type for x in type(obj).mro())
        except TypeError:
            return False


class FastTensorEncoder(TensorEncoder):
    fast_bytes = True


def best_effort_to_bytes(obj):
    if type(obj).__module__ == "torch" and type(obj).__name__ == "Tensor":
        if obj.is_cuda:
            obj = obj.cpu()
        obj = obj.detach().numpy()
    if type(obj).__module__ == "numpy":
        if type(obj).__name__ == "dtype":
            obj = str(obj).encode("utf-8")
        else:
            obj = obj.tostring()
    return obj


def stringify(obj, *, fast_bytes=False):
    return json.dumps(
        obj, cls=FastTensorEncoder if fast_bytes else TensorEncoder, sort_keys=True
    )


def stable_hash(obj, *, fast_bytes=True):
    return hashlib.sha256(
        stringify(obj, fast_bytes=fast_bytes).encode("utf-8")
    ).hexdigest()
