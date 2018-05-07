"""
Test importing Wagtail pages.
"""
import textwrap

from django.test import TestCase
from wagtail.core.models import Site
from wagtail.images.models import Image

from .app.models import BasicSetting
from .base import ImporterTestCaseMixin, fresh_media_root


class TestSettingsImport(ImporterTestCaseMixin, TestCase):
    """Test importing Wagtail sites."""
    def import_site(self, hostname='example.com'):
        """Make a site with a hostname to create settings for."""
        doc = textwrap.dedent(
            """
            url: /my-home/
            type: app.basicpage
            title: Home page

            ---

            !site
                hostname: {hostname}
                site_name: "Example website"
                root_page: !page
                    url: /my-home/
                is_default_site: True
            """
        ).format(hostname=hostname)
        self.run_import(doc)
        return Site.objects.get(hostname=hostname)

    def test_basic_import(self):
        """Test importing a simple setting."""
        site = self.import_site()
        doc = textwrap.dedent(
            """
            !app.basicsetting
                site: !site { hostname: example.com }
                text: Hello, world!
            """
        )
        self.run_import(doc)

        setting = BasicSetting.objects.get(site=site)
        self.assertEqual(setting.text, "Hello, world!")

    @fresh_media_root()
    def test_foreign_keys(self):
        """Test importing settings that have foreign keys to other models."""
        site = self.import_site()
        doc = textwrap.dedent(
            """
            !image
                file: suunn.jpg
                title: Sunny sun dog

            ---

            !app.basicsetting
                site: !site { hostname: example.com }
                cute_dog: !image { file: suunn.jpg }
            """
        )
        self.run_import(doc)

        setting = BasicSetting.objects.get(site=site)
        image = Image.objects.get()
        self.assertEqual(setting.cute_dog, image)

    @fresh_media_root()
    def test_update(self):
        """Test updating a site instance, preserving old fields."""
        site = self.import_site()
        doc = textwrap.dedent(
            """
            !app.basicsetting
                site: !site { hostname: example.com }
                text: Hello, world!
            """
        )
        self.run_import(doc)

        doc = textwrap.dedent(
            """
            !image
                file: suunn.jpg
                title: Sunny sun dog

            ---

            !app.basicsetting
                site: !site { hostname: example.com }
                cute_dog: !image { file: suunn.jpg }
            """
        )
        self.run_import(doc)

        setting = BasicSetting.objects.get(site=site)
        image = Image.objects.get()
        self.assertEqual(setting.text, "Hello, world!")
        self.assertEqual(setting.cute_dog, image)
