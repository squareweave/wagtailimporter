"""
Import pages into Wagtail
"""
import json
import os
from pathlib import Path, PurePosixPath

import yaml
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.core.fields import StreamField
from wagtail.core.models import Page

from ... import serializer
from ...serializer import normalise


class Command(BaseCommand):
    """
    Import pages into Wagtail.
    """

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='+', type=str)

    @transaction.atomic
    def handle(self, *args, **options):
        for filename in options['file']:
            with open(filename) as file_:
                docs = yaml.safe_load_all(file_)
                self.stdout.write("Reading %s" % filename)

                cwd = Path.cwd()
                try:
                    os.chdir(str(Path(filename).parent))
                    self.import_documents(docs)
                finally:
                    os.chdir(str(cwd))

    @transaction.atomic
    def import_documents(self, docs):
        """Import a Yaml file of documents."""

        for doc in docs:
            try:
                if isinstance(doc, serializer.GetForeignObject):
                    self.import_snippet(doc)
                else:
                    self.import_page(doc)
            except CommandError as exc:
                self.stderr.write("Error importing page: %s" % exc)

    @transaction.atomic
    def import_snippet(self, data):
        """Import a snippet (which is a GetForeignObject)."""

        obj = data.__to_value__()
        self.stdout.write("Importing %s %s" % (obj._meta.verbose_name, obj))
        obj.save()

    @transaction.atomic
    def import_page(self, data):
        """Import a single wagtail page."""
        model = self.get_page_model_class(data)
        self.find_page(model, data)

    def get_page_model_class(self, data):
        """
        Get the page model class from the `type' parameter.
        """

        try:
            type_ = data.pop('type')
        except KeyError:
            raise CommandError("Need `type' for page")

        try:
            app_label, model = type_.split('.')
            return ContentType.objects.get(app_label=app_label,
                                           model=model)\
                .model_class()
        except (ValueError, AttributeError):
            raise CommandError("`type' is of form `app.model'")
        except ContentType.DoesNotExist:
            raise CommandError("Unknown page type `%s'" % type_)

    def find_page(self, model, data):
        """
        Find a page by its URL and import its data.

        Data importing has to be done here because often the page can't
        be saved until the data is imported (i.e. null fields)
        """
        try:
            url = PurePosixPath(data.pop('url'))
            if not url.is_absolute():
                raise CommandError("Path %s must be absolute" % url)

        except KeyError:
            raise CommandError("Need `url' for page")

        try:
            page = model.objects.get(url_path=normalise(url))
            self.import_data(page, data)
            page.save()
            self.stdout.write("Updating existing page %s" % url)
        except model.DoesNotExist:
            try:
                # pylint:disable=no-member
                parent = Page.objects.get(url_path=normalise(url.parent))
            except Page.DoesNotExist:
                raise CommandError("Parent of %s doesn't exist" % url)

            page = model(slug=url.name)
            self.import_data(page, data)
            parent.add_child(instance=page)
            self.stdout.write("Creating new page %s" % url)

        return page

    def import_data(self, page, data):
        """Import the data onto a page."""

        for key, value in data.items():
            try:
                field = page._meta.get_field(key)

                if isinstance(field, StreamField):
                    value = json.dumps(value, cls=serializer.JSONEncoder)
                else:
                    # Assume we know how to serialise it
                    pass

            except FieldDoesNotExist:
                # This might be a property, just try and set it anyway
                pass

            value = serializer.FieldStorable.to_objects(value)

            setattr(page, key, value)
