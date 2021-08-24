
# Permacache

Add a permanant disk-backed cache for a given function.

## Simple usage

```
from permacache import permacache

@permacache("unique/path/for/this/function")
def f(x):
    out = x ** 2 # do some fancy compute here
    return out
```

You can simply annotate your function with the permacache annotation as shown above

## Compressing arguments

By default, permacache uses a full json stringification of the arguments of your function, with a few special cases given to numpy, torch, and attr classes. If you want to use other classes or only use part of an argument as a key, you can pass in a key_function as such

```
from permacache import permacache, stable_hash
@permacache(
    "path",
    key_function=dict(large_argument=stable_hash, not_json_argument=lambda x: str(x), transient_flag=None)
)
def f(large_argument, not_json_argument, transient_flag):
    ...
```

The dictionary has keys that correspond to each of the arguments, and the values are applied to them before placing them in the key. Here, `stable_hash` can be used to hash the json stringification of the value, saving disk space but making recovering the value impossible if you want to do that later. Additionally, `str` can be used to stringify objects that you are convinced have stable `str` representations but cannot be represented in json. Finally, the flag argument is ignored in the JSON representation, this is useful for verbosity flags, etc., that don't affect the output.

## Aliasing

Permacache uses the underlying function signature to construct the key. For example, for the function

```
@permacache("path/f")
def f(x, y=2, z=3):
    pass
```

The calls `f(2)`, `f(2, 2, 3)`, `f(2, z=3, y=2)`, and `f(x=2, y=2, z=3)` are all cached using the same key.

If you want to add an extra argument, you can keep backwards compatibility using the following code.

```
from permacache import drop_if_equal

@permacache("path/f", key_function=dict(t=drop_if_equal(0)))
def f(x, y=2, z=3, t=0):
    pass
```

In the above code, `t` is dropped from consideration if `t == 0`, allowing us to reuse our old calls.