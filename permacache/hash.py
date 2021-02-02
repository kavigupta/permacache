import json
import hashlib


class TensorEncoder(json.JSONEncoder):
    fast_bytes = False

    def default(self, obj):
        original = obj
        if hasattr(obj, "__attrs_attrs__"):
            typename = type(obj).__name__
            obj = {a.name: getattr(obj, a.name) for a in obj.__attrs_attrs__}
            obj[".attr.__name__"] = typename
        obj = best_effort_to_bytes(obj)
        if isinstance(obj, bytes):
            if self.fast_bytes:
                obj = hashlib.sha256(obj).hexdigest()
            else:
                obj = str(obj)
        if obj is original:
            return super().default(obj)
        return obj


class FastTensorEncoder(TensorEncoder):
    fast_bytes = True


def best_effort_to_bytes(obj):
    if type(obj).__module__ == "torch" and type(obj).__name__ == "Tensor":
        if obj.is_cuda:
            obj = obj.cpu()
        obj = obj.detach().numpy()
    if type(obj).__module__ == "numpy":
        obj = obj.tostring()
    return obj


def stringify(obj, *, fast_bytes=False):
    return json.dumps(
        obj, cls=FastTensorEncoder if fast_bytes else TensorEncoder, sort_keys=True
    )


def stable_hash(obj, **kwargs):
    return hashlib.sha256(stringify(obj, **kwargs).encode("utf-8")).hexdigest()
