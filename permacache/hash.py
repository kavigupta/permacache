import json
import hashlib


class TensorEncoder(json.JSONEncoder):
    def default(self, obj):
        original = obj
        if type(obj).__module__ == "torch" and type(obj).__name__ == "Tensor":
            if obj.is_cuda:
                obj = obj.cpu()
            obj = obj.detach().numpy()
        if type(obj).__module__ == "numpy":
            obj = str(obj.tostring())
        if hasattr(obj, "__attrs_attrs__"):
            typename = type(obj).__name__
            obj = {a.name: getattr(obj, a.name) for a in obj.__attrs_attrs__}
            obj[".attr.__name__"] = typename
        if obj is original:
            return super().default(obj)
        return obj


def stringify(obj):
    return json.dumps(obj, cls=TensorEncoder, sort_keys=True)


def stable_hash(obj):
    return hashlib.sha256(stringify(obj).encode("utf-8")).hexdigest()
