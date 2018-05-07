"""
Test importing Wagtail pages.
"""
import textwrap
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from wagtail.images.models import Image

from .base import ImporterTestCaseMixin, fresh_media_root


class TestImageImport(ImporterTestCaseMixin, TestCase):
    """Test importing Wagtail images."""

    @fresh_media_root()
    def test_basic_import(self):
        """Test importing a single image."""
        doc = textwrap.dedent(
            """
            !image
                title: Floral doge
                file: floral.jpeg
            """
        )
        self.run_import(doc)

        image = Image.objects.get()
        self.assertEqual(image.title, "Floral doge")
        self.assertEqual(image.file.name, 'original_images/images/floral.jpeg')

        # Check the file imported correctly
        original_filename = self.get_import_dir() / 'images/floral.jpeg'
        with image.file as imported:
            with open(str(original_filename), 'rb') as original:
                self.assertEqual(imported.read(), original.read())

    @fresh_media_root()
    def test_update(self):
        """Test updating an image."""
        doc = textwrap.dedent(
            """
            !image
                title: Floral doge
                file: lazors.jpg
            """
        )
        self.run_import(doc)
        image = Image.objects.get()
        self.assertEqual(image.title, "Floral doge")
        self.assertEqual(image.file.name, 'original_images/images/lazors.jpg')

        doc = textwrap.dedent(
            """
            !image
                title: Dog and flowers
                file: lazors.jpg
            """
        )
        self.run_import(doc)

        image.refresh_from_db()
        # The title should have updated
        self.assertEqual(image.title, "Dog and flowers")
        # The filename should not have changed
        self.assertEqual(image.file.name, 'original_images/images/lazors.jpg')
        # Check that there is still only a single image in MEDIA_ROOT
        file_path = Path(settings.MEDIA_ROOT) / Path(image.file.name)
        directory = file_path.parent
        self.assertEqual(
            list(directory.iterdir()),  # pylint:disable=no-member
            [file_path])

    @fresh_media_root()
    def test_spaces_in_filename(self):
        """Test importing an images with spaces in the filename."""
        doc = textwrap.dedent(
            """
            !image
                title: Hidden doge, sleeping whippet
                file: "hidden doge sleeping whippet.jpg"
            """
        )
        self.run_import(doc)
        filename = Path('images/hidden doge sleeping whippet.jpg')

        image = Image.objects.get()
        self.assertEqual(Path(image.file.name),
                         Path('original_images') / filename)
