"""
Test importing Wagtail pages.
"""
import textwrap

from django.test import TestCase

from .app.models import BasicPage, ForeignKeyPage
from .base import ImporterTestCaseMixin


class TestPageImport(ImporterTestCaseMixin, TestCase):
    """Test importing Wagtail pages."""
    def test_basic_import(self):
        """Test importing some simple nested pages."""
        doc = textwrap.dedent(
            """
            url: /page/
            type: app.basicpage
            title: Basic import
            show_in_menus: true
            body: Hello, world!

            ---

            url: /page/child/
            type: app.basicpage
            title: Child page
            """
        )
        self.run_import(doc)

        self.assertEqual(BasicPage.objects.count(), 2)

        page = BasicPage.objects.get(url_path='/page/')
        self.assertEqual(page.title, "Basic import")
        self.assertEqual(page.slug, 'page')
        self.assertTrue(page.show_in_menus)
        self.assertEqual(page.body, "Hello, world!")

        child = BasicPage.objects.child_of(page).get()
        self.assertEqual(child.url_path, '/page/child/')
        self.assertEqual(child.slug, 'child')
        self.assertEqual(child.title, "Child page")

    def test_update(self):
        """
        Test updating an existing page with new fields.
        """
        doc = textwrap.dedent(
            """
            url: /page/
            type: app.basicpage
            title: Initial title
            """
        )
        self.run_import(doc)

        page = BasicPage.objects.get()
        self.assertEqual(page.title, "Initial title")

        doc = textwrap.dedent(
            """
            url: /page/
            type: app.basicpage
            title: New title
            """
        )
        self.run_import(doc)

        page.refresh_from_db()
        self.assertEqual(page.title, "New title")

    def test_page_foreign_key(self):
        """Test importing some simple nested pages."""
        doc = textwrap.dedent(
            """
            url: /target/
            type: app.basicpage
            title: Target page

            ---

            url: /source/
            type: app.foreignkeypage
            title: Source page
            other_page: !page { url: /target/ }
            """
        )
        self.run_import(doc)

        target = BasicPage.objects.get()
        source = ForeignKeyPage.objects.get()

        self.assertEqual(source.other_page.specific, target)

    def test_deferred_foreign_key(self):
        """Test importing some simple nested pages."""
        doc = textwrap.dedent(
            """
            url: /parent/
            type: app.foreignkeypage
            title: Parent page

            ---

            url: /parent/child/
            type: app.basicpage
            title: Child page

            ---

            url: /parent/
            type: app.foreignkeypage
            other_page: !page { url: /parent/child/ }
            """
        )
        self.run_import(doc)

        parent = ForeignKeyPage.objects.get()
        child = BasicPage.objects.child_of(parent).get()

        self.assertEqual(parent.other_page.specific, child)

    def test_other_pages_untouched(self):
        """Test that pages not part of the import are untouched."""
        doc = textwrap.dedent(
            """
            url: /page/
            type: app.basicpage
            title: Basic page
            """
        )
        self.run_import(doc)

        page = BasicPage.objects.get()
        page.title = "New title"
        page.save()

        child = page.add_child(instance=BasicPage(
            title="Child page",
            slug="child",
        ))

        self.run_import(doc)

        page.refresh_from_db()
        self.assertEqual(page.title, "Basic page")
        self.assertTrue(BasicPage.objects.filter(pk=child.pk).exists())
