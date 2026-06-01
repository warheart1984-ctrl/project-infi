"""Tests for runtime-safe logger setup."""

import unittest

import src.logger as logger_module


class TestLoggerStreams(unittest.TestCase):
    """Ensure detached Windows launches still provide usable stdio handles."""

    def test_ensure_standard_streams_creates_fallbacks(self):
        """pythonw-style launches should get writable fallback stdout/stderr objects."""
        original_stdout = logger_module.sys.stdout
        original_stderr = logger_module.sys.stderr

        try:
            logger_module.sys.stdout = None
            logger_module.sys.stderr = None
            logger_module._STDOUT_FALLBACK = None
            logger_module._STDERR_FALLBACK = None

            logger_module.ensure_standard_streams()

            self.assertIsNotNone(logger_module.sys.stdout)
            self.assertIsNotNone(logger_module.sys.stderr)
            self.assertTrue(hasattr(logger_module.sys.stderr, "isatty"))
        finally:
            if logger_module._STDOUT_FALLBACK is not None:
                logger_module._STDOUT_FALLBACK.close()
                logger_module._STDOUT_FALLBACK = None
            if logger_module._STDERR_FALLBACK is not None:
                logger_module._STDERR_FALLBACK.close()
                logger_module._STDERR_FALLBACK = None

            logger_module.sys.stdout = original_stdout
            logger_module.sys.stderr = original_stderr

    def test_ensure_standard_streams_replaces_unusable_streams(self):
        """Detached launches with broken inherited handles should be repaired."""

        class BrokenStream:
            def write(self, _value):
                raise OSError(22, "Invalid argument")

            def flush(self):
                raise OSError(22, "Invalid argument")

        original_stdout = logger_module.sys.stdout
        original_stderr = logger_module.sys.stderr

        try:
            logger_module.sys.stdout = BrokenStream()
            logger_module.sys.stderr = BrokenStream()
            logger_module._STDOUT_FALLBACK = None
            logger_module._STDERR_FALLBACK = None

            logger_module.ensure_standard_streams()

            self.assertIsNotNone(logger_module.sys.stdout)
            self.assertIsNotNone(logger_module.sys.stderr)
            self.assertTrue(hasattr(logger_module.sys.stdout, "write"))
            self.assertTrue(hasattr(logger_module.sys.stderr, "write"))
        finally:
            if logger_module._STDOUT_FALLBACK is not None:
                logger_module._STDOUT_FALLBACK.close()
                logger_module._STDOUT_FALLBACK = None
            if logger_module._STDERR_FALLBACK is not None:
                logger_module._STDERR_FALLBACK.close()
                logger_module._STDERR_FALLBACK = None

            logger_module.sys.stdout = original_stdout
            logger_module.sys.stderr = original_stderr


if __name__ == "__main__":
    unittest.main()
