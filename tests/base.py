"""
Base test class for testing the import_pages command
"""

import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from django.core.management import call_command
from django.test import override_settings


class ImporterTestCaseMixin(object):
    """
    TestCase mixin for testing the import_pages management command.
    """
    def run_import(self, yaml,
                   **kwargs):
        """
        Run an import with the supplied YAML document. ``stdout`` and
        ``stderr`` are silenced by default, pass in an ``io.StringIO`` instance
        as a kwarg if you want to collect either.
        """
        with NamedTemporaryFile('w+', dir=str(self.get_import_dir())) as temp:
            temp.write(yaml)
            temp.seek(0)

            kwargs.setdefault('stdout', open(os.devnull, 'w'))
            kwargs.setdefault('stderr', open(os.devnull, 'w'))
            call_command('import_pages', temp.name, **kwargs)

    def get_import_dir(self):
        """Where to run the import from."""
        return Path(__file__).parent / 'import_data'


@contextmanager
def fresh_media_root(**kwargs):
    """
    Run a test with a fresh, empty MEDIA_ROOT temporary directory.
    """
    with TemporaryDirectory(**kwargs) as media_root:
        with override_settings(MEDIA_ROOT=media_root):
            yield
