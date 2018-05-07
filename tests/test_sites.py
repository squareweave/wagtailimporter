"""
Test importing Wagtail pages.
"""
import textwrap

from django.test import TestCase
from wagtail.core.models import Site

from .app.models import BasicPage
from .base import ImporterTestCaseMixin


class TestSiteImport(ImporterTestCaseMixin, TestCase):
    """Test importing Wagtail sites."""
    def test_basic_import(self):
        """Test importing some simple nested pages."""
        doc = textwrap.dedent(
            """
            url: /my-home/
            type: app.basicpage
            title: Home page

            ---

            !site
                hostname: example.com
                site_name: "Example website"
                root_page: !page { url: /my-home/ }
                is_default_site: True
            """
        )
        self.run_import(doc)

        page = BasicPage.objects.get()
        site = Site.objects.get(hostname='example.com')
        self.assertEqual(site.root_page.specific, page)
        self.assertEqual(site.site_name, "Example website")

    def test_update(self):
        """Test updating a site instance."""
        doc = textwrap.dedent(
            """
            url: /my-home/
            type: app.basicpage
            title: Home page

            ---

            !site
                hostname: example.com
                site_name: "Example website"
                root_page: !page { url: /my-home/ }
                is_default_site: True
            """
        )
        self.run_import(doc)

        # Check everything imported sensibly
        home = BasicPage.objects.get()
        site = Site.objects.get(hostname='example.com')
        self.assertEqual(site.root_page.specific, home)
        self.assertEqual(site.site_name, "Example website")

        doc = textwrap.dedent(
            """
            url: /new-home/
            type: app.basicpage
            title: New home page

            ---

            !site
                hostname: example.com
                site_name: "New example website"
                root_page: !page { url: /new-home/ }
                is_default_site: True
            """
        )
        self.run_import(doc)

        # Get new data
        new_home = BasicPage.objects.get(url_path='/new-home/')
        site.refresh_from_db()

        # The site should have a new home page
        self.assertEqual(site.root_page.specific, new_home)

        # Check the old page still exists
        self.assertTrue(BasicPage.objects.filter(pk=home.pk).exists())
