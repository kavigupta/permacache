
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

**Extremely important note**: If you use `stable_hash`, it is only guaranteed to be stable for the same major version of `numpy` (numpy `1.*.*` vs `2.*.*`) and the same operating system. On Ubuntu it does appear to be stable across versions of `numpy`, but this is not true on Mac OS.

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

## Out Files

You can specify one or more input parameters to be the "out files" of the function. These are files
    that the function creates and writes to. If the function is called with the same arguments except
    for these paths, the function will not be recomputed, so long as some path still exists that was
    written to by this function historically. This is useful for functions whose output is writing
    to a file rather than returning a value. The function can also have a return value, which is
    cached normally.

You are responsible for ensuring that the output parameter is not used in the body of the function
    except for writing to it.

This feature is not supported on Windows.

```python
@permacache("path/f", out_file=["loc"])
def f(x, loc):
    with open(loc, "w") as f:
        f.write(str(x) * 10000)
    return [x]
```