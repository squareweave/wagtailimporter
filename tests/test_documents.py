"""
Test importing Wagtail pages.
"""
import textwrap
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from wagtail.documents.models import Document

from .base import ImporterTestCaseMixin, fresh_media_root


class TestDocumentImport(ImporterTestCaseMixin, TestCase):
    """Test importing Wagtail documents."""

    @fresh_media_root()
    def test_basic_import(self):
        """Test importing a single document."""
        doc = textwrap.dedent(
            """
            !document
                title: Annual report
                file: hello-world.txt
            """
        )
        self.run_import(doc)

        document = Document.objects.get()
        self.assertEqual(document.title, "Annual report")
        self.assertEqual(document.file.name, "documents/hello-world.txt")

        # Check the file imported correctly
        original_filename = self.get_import_dir() / 'documents/hello-world.txt'
        with document.file as imported:
            with open(str(original_filename), 'rb') as original:
                self.assertEqual(imported.read(), original.read())

    @fresh_media_root()
    def test_update(self):
        """Test updating an document."""
        doc = textwrap.dedent(
            """
            !document
                title: Annual report
                file: hello-world.txt
            """
        )
        self.run_import(doc)
        document = Document.objects.get()
        self.assertEqual(document.title, "Annual report")
        self.assertEqual(document.file.name, 'documents/hello-world.txt')

        doc = textwrap.dedent(
            """
            !document
                title: Annual report 2018
                file: hello-world.txt
            """
        )
        self.run_import(doc)

        document.refresh_from_db()
        # The title should have updated
        self.assertEqual(document.title, "Annual report 2018")
        # The filename should not have changed
        self.assertEqual(document.file.name, 'documents/hello-world.txt')
        # Check that there is still only a single document in MEDIA_ROOT
        file_path = Path(settings.MEDIA_ROOT) / Path(document.file.name)
        directory = file_path.parent
        self.assertEqual(
            list(directory.iterdir()),  # pylint:disable=no-member
            [file_path])
