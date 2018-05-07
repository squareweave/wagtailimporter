#!/usr/bin/env python
"""Set up the test environment and run the tests for wagtailimporter."""

import os
import sys
import warnings


def run():
    """Run the tests."""
    from django.core.management import execute_from_command_line
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.app.settings'
    os.environ.setdefault('DATABASE_NAME', ':memory:')
    warnings.filterwarnings('always', module='wagtailnews', category=DeprecationWarning)
    warnings.filterwarnings('always', module='wagtailnews', category=PendingDeprecationWarning)
    execute_from_command_line([sys.argv[0], 'test'] + sys.argv[1:])


if __name__ == '__main__':
    run()
