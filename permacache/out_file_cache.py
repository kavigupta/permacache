from dataclasses import dataclass
import os
import shutil


@dataclass
class OutFile:
    path: str


def process_out_file_parameter(key_function, parallel, out_file):
    if isinstance(out_file, str):
        out_file = (out_file,)
    if isinstance(out_file, list):
        out_file = tuple(out_file)
    if not isinstance(out_file, tuple) or not all(isinstance(o, str) for o in out_file):
        raise ValueError("`out` must be a string or tuple of strings")
    if parallel:
        raise ValueError("`out` and `parallel` cannot be used together")
    if not isinstance(key_function, dict):
        raise ValueError("`out` requires `key_function` to be a dict")
    key_function = {**key_function, **{o: OutFile for o in out_file}}

    return out_file, key_function


def remove_out_files(key_full):
    key = {k: v for k, v in key_full.items() if not isinstance(v, OutFile)}
    out_files = {k: v.path for k, v in key_full.items() if isinstance(v, OutFile)}
    return key, out_files


def do_copy_files(file_cache_info, out_files):
    for param in out_files:
        if param not in file_cache_info:
            return file_cache_info, False
        file_cache_info[param], success = do_copy_file(
            file_cache_info[param], out_files[param]
        )
        if not success:
            return file_cache_info, False
    return file_cache_info, True


def do_copy_file(file_cache, out_path):
    file_cache_valid = {}
    for path in file_cache:
        try:
            good = os.stat(path).st_mtime_ns == file_cache[path]
            if good:
                file_cache_valid[path] = file_cache[path]
        except FileNotFoundError:
            pass
    print(file_cache, file_cache_valid)
    if out_path in file_cache_valid:
        return file_cache_valid, True
    if not file_cache_valid:
        return file_cache_valid, False
    path = min(file_cache_valid)
    shutil.copy(path, out_path)
    decrement_mtime_ns(out_path)
    file_cache_valid[out_path] = os.stat(out_path).st_mtime_ns
    return file_cache_valid, True


def decrement_mtime_ns(path):
    # decrementing mtime is necessary for some dumb reason. See https://stackoverflow.com/q/78525411/1549476
    # so that this doesn't lead to conflicts when writing to the same file multiple times we cycle the decrement,
    # at about 10k we recycle. This corresponds to 10us, which should be shorter than the true time between
    # filesystem writes.
    decrement = getattr(decrement_mtime_ns, "decrement", 0)
    decrement += 1
    if decrement > 10000:
        decrement = 1
    decrement_mtime_ns.decrement = decrement
    stat = os.stat(path)
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns - decrement))


def add_file_cache_info(file_cache_info, out_files):
    for param in out_files:
        decrement_mtime_ns(out_files[param])

    return {
        param: {
            **file_cache_info.get(param, {}),
            out_files[param]: os.stat(out_files[param]).st_mtime_ns,
        }
        for param in out_files
    }
