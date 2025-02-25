import enum
import hashlib
import json
import numbers
from types import SimpleNamespace


class TensorEncoder(json.JSONEncoder):
    fast_bytes = False

    def default(self, o):
        original = o
        if hasattr(type(o), "__permacache_hash__"):
            o = {".custom": True, "content": type(o).__permacache_hash__(o)}
        if hasattr(o, "__attrs_attrs__"):
            typename = type(o).__name__
            o = {a.name: getattr(o, a.name) for a in o.__attrs_attrs__}
            o[".attr.__name__"] = typename
        if hasattr(o, "__dataclass_fields__"):
            typename = type(o).__name__
            is_migrated_attrs = getattr(o, "_migrated_attrs", False)
            o = {a: getattr(o, a) for a in o.__dataclass_fields__}
            if is_migrated_attrs:
                o[".attr.__name__"] = typename
            else:
                o[".dataclass.__name__"] = typename
        if isinstance(o, SimpleNamespace):
            o = o.__dict__
            o[".builtin.__name__"] = "types.SimpleNamespace"
        if (
            type(o).__module__ == "torch.nn.parameter"
            and type(o).__name__ == "Parameter"
        ):
            o = o.data
        o = best_effort_to_bytes(o)
        if isinstance(o, bytes):
            if self.fast_bytes:
                o = hashlib.sha256(o).hexdigest()
            else:
                o = str(o)
        if isinstance(o, range):
            o = {".type": "range", "representation": str(o)}
        if isinstance(o, type):
            o = {".type": "type", "name": o.__module__ + "." + o.__qualname__}
        if self.isinstance_str(o, "Module"):
            o = {
                ".type": "Module",
                "hash": dict(
                    other_dict={
                        k: v for k, v in o.__dict__.items() if not k.startswith("_")
                    },
                    state_dict=o.state_dict(),
                ),
            }
        if self.isinstance_str(o, "DataFrame"):
            return {
                ".type": "pandas.DataFrame",
                "columns": list(o),
                "values": {k: o[k] for k in o},
            }
        if self.isinstance_str(o, "Series"):
            return {
                ".type": "pandas.Series",
                "index": list(o.index),
                "values": list(o),
            }
        if isinstance(o, enum.Enum):
            return {
                ".type": "enum",
                "enum.name": type(o).__name__,
                "enum.value": o.value,
            }
        o = fix_dictionary(o)
        if o is original:
            return super().default(o)
        return o

    def isinstance_str(self, obj, str_type):
        try:
            return any(x.__name__ == str_type for x in type(obj).mro())
        except TypeError:
            return False


def fix_dictionary(obj):
    """
    Fix dictionaries with non-json keys.
    """
    if isinstance(obj, (list, tuple)):
        return [fix_dictionary(x) for x in obj]
    if not isinstance(obj, dict):
        return obj
    if any(not isinstance(k, (str, numbers.Number)) for k in obj.keys()):
        obj = {
            ".fixed_dictionary_nonjson_keys": True,
            "contents": {stringify(k, fast_bytes=True): v for k, v in obj.items()},
        }
    obj = {k: fix_dictionary(v) for k, v in obj.items()}
    return obj


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
            obj = obj.tobytes()
    return obj


def stringify(obj, *, fast_bytes=False):
    u = json.dumps(
        fix_dictionary(obj),
        cls=FastTensorEncoder if fast_bytes else TensorEncoder,
        sort_keys=True,
    )
    print(u)
    return u


def stable_hash(obj, *, fast_bytes=True):
    return hashlib.sha256(
        stringify(obj, fast_bytes=fast_bytes).encode("utf-8")
    ).hexdigest()


def migrated_attrs(cls):
    """
    Decorator to mark a class as having been migrated from attrs to dataclasses.
    """
    # pylint: disable=protected-access
    cls._migrated_attrs = True
    return cls
