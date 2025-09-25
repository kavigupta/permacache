import io
import os
import tempfile
import unittest
from unittest.mock import patch

from permacache import cache
from permacache.locked_shelf import sync_all_caches, close_all_caches
from permacache.main import count_keys_in_cache, do_count


# pylint: disable=keyword-arg-before-vararg
def fn(x, y=2, z=3, *args):
    fn.counter += 1
    return x, y, z, args


class CountTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for cache
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_cache = cache.CACHE
        cache.CACHE = self.temp_dir.name
        fn.counter = 0

    def tearDown(self):
        close_all_caches()
        cache.CACHE = self.original_cache
        self.temp_dir.cleanup()

    def _flush_caches(self):
        """Flush all caches to disk before counting."""
        sync_all_caches()
        close_all_caches()

    def test_count_combined_file_cache(self):
        """Test counting keys in a combined-file cache."""
        # Create a cached function
        cached_fn = cache.permacache("test_cache")(fn)

        # Add some entries to the cache
        cached_fn(1, 2, 3)
        cached_fn(4, 5, 6)
        cached_fn(7, 8, 9)

        self._flush_caches()

        # Count the keys
        cache_path = os.path.join(cache.CACHE, "test_cache")
        count = count_keys_in_cache(cache_path)

        self.assertEqual(count, 3)

    def test_count_empty_cache(self):
        """Test counting keys in an empty cache."""
        # Create a cached function but don't call it
        cache.permacache("empty_cache")(fn)

        self._flush_caches()

        # Count the keys
        cache_path = os.path.join(cache.CACHE, "empty_cache")
        count = count_keys_in_cache(cache_path)

        self.assertEqual(count, 0)

    def test_count_nonexistent_cache(self):
        """Test error handling for non-existent cache."""
        cache_path = os.path.join(cache.CACHE, "nonexistent_cache")

        with self.assertRaises(RuntimeError) as context:
            count_keys_in_cache(cache_path)

        self.assertIn("Cache does not exist", str(context.exception))

    def test_do_count_function(self):
        """Test the do_count function with proper output."""
        # Create a cached function and add entries
        cached_fn = cache.permacache("test_do_count")(fn)
        cached_fn(1, 2, 3)
        cached_fn(4, 5, 6)

        self._flush_caches()

        # Mock args object
        class MockArgs:
            cache_name = "test_do_count"

        args = MockArgs()

        # Mock the cache directory to use our test directory
        with patch("appdirs.user_cache_dir", return_value=cache.CACHE):
            # Capture stdout
            captured_output = io.StringIO()
            with patch("sys.stdout", captured_output):
                do_count(args)

            output = captured_output.getvalue()
            self.assertIn("Cache 'test_do_count' contains 2 keys", output)

    def test_do_count_error_handling(self):
        """Test error handling in do_count function."""

        # Mock args object with non-existent cache
        class MockArgs:
            cache_name = "nonexistent_cache"

        args = MockArgs()

        # Capture stderr and test exit code
        captured_stderr = io.StringIO()
        with patch("sys.stderr", captured_stderr), patch("sys.exit") as mock_exit:
            do_count(args)

        error_output = captured_stderr.getvalue()
        self.assertIn("Error: Cache does not exist", error_output)
        mock_exit.assert_called_once_with(1)

    def test_count_with_different_key_types(self):
        """Test counting with different types of keys."""
        # Create a cached function
        cached_fn = cache.permacache("mixed_keys_cache")(fn)

        # Add entries with different argument patterns
        cached_fn(1, 2, 3)  # positional args
        cached_fn(x=10, y=20, z=30)  # keyword args
        cached_fn(100, z=300)  # mixed args

        self._flush_caches()

        # Count the keys
        cache_path = os.path.join(cache.CACHE, "mixed_keys_cache")
        count = count_keys_in_cache(cache_path)

        self.assertEqual(count, 3)

    def test_count_with_parallel_cache(self):
        """Test counting keys in a cache with parallel processing."""

        # Create a cached function with parallel processing
        def parallel_fn(xs, y, z):
            fn.counter += len(xs)
            return [(x + y + z) for x in xs]  # Return a list for each x

        cached_fn = cache.permacache("parallel_cache", parallel=("xs",))(parallel_fn)

        # Add entries
        cached_fn(xs=[1, 2, 3], y=10, z=20)

        self._flush_caches()

        # Count the keys (should be 3 due to parallel processing)
        cache_path = os.path.join(cache.CACHE, "parallel_cache")
        count = count_keys_in_cache(cache_path)

        self.assertEqual(count, 3)


class CountCLITest(unittest.TestCase):
    """Test the CLI interface for the count command."""

    def setUp(self):
        # Create a temporary directory for cache
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_cache = cache.CACHE
        cache.CACHE = self.temp_dir.name
        fn.counter = 0

    def tearDown(self):
        close_all_caches()
        cache.CACHE = self.original_cache
        self.temp_dir.cleanup()

    def _flush_caches(self):
        """Flush all caches to disk before counting."""
        sync_all_caches()
        close_all_caches()

    def test_count_command_help(self):
        """Test that count command shows help correctly."""
        from permacache.main import main

        # Capture stdout
        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output), patch(
            "sys.argv", ["permacache", "count", "--help"]
        ):
            try:
                main()
            except SystemExit:
                pass  # argparse calls sys.exit() for help

        output = captured_output.getvalue()
        self.assertIn("cache_name", output)

    def test_count_command_with_cache(self):
        """Test count command with an actual cache."""
        from permacache.main import main

        # Create a cached function and add entries
        cached_fn = cache.permacache("cli_test_cache")(fn)
        cached_fn(1, 2, 3)
        cached_fn(4, 5, 6)

        self._flush_caches()

        # Mock the cache directory to use our test directory
        with patch("appdirs.user_cache_dir", return_value=cache.CACHE):
            # Capture stdout
            captured_output = io.StringIO()
            with patch("sys.stdout", captured_output), patch(
                "sys.argv", ["permacache", "count", "cli_test_cache"]
            ):
                main()

            output = captured_output.getvalue()
            self.assertIn("Cache 'cli_test_cache' contains 2 keys", output)

    def test_count_command_nonexistent_cache(self):
        """Test count command with non-existent cache."""
        from permacache.main import main

        # Capture stderr
        captured_stderr = io.StringIO()
        with patch("sys.stderr", captured_stderr), patch(
            "sys.argv", ["permacache", "count", "nonexistent_cache"]
        ):
            try:
                main()
            except SystemExit:
                pass  # do_count calls sys.exit(1) for errors

        error_output = captured_stderr.getvalue()
        self.assertIn("Error: Cache does not exist", error_output)


if __name__ == "__main__":
    unittest.main()
