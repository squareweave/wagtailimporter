"""
Objects for YAML serializer/deserializer
"""
import os
import json
import logging
from pathlib import PurePosixPath

import yaml
from unidecode import unidecode

from django.core.files import File
from django.db import transaction
from wagtail.wagtailcore.models import Page as WagtailPage
from wagtail.wagtailimages.models import Image as WagtailImage

LOGGER = logging.getLogger(__name__)


class JSONSerializable(object):
    """Interface to objects which are serializable into JSON."""

    def __to_json__(self):
        """Serialize to JSON."""
        raise NotImplementedError()


class FieldStorable(object):
    """Interface to objects which can be stored in Django model fields."""

    def __to_value__(self):
        """Value to store in a Django model."""
        raise NotImplementedError()


class JSONEncoder(json.JSONEncoder):
    """
    Extension of the JSON encoder that knows how to encode the YAML objects
    """

    def default(self, obj):  # pylint:disable=method-hidden
        if isinstance(obj, JSONSerializable):
            return obj.__to_json__()

        return super().default(obj)


class GetForeignObject(FieldStorable, yaml.YAMLObject):
    """
    Get a foreign key reference for the provided parameters
    """

    yaml_loader = yaml.SafeLoader

    @property
    def model(self):
        """Model for this reference."""
        raise NotImplementedError()

    @property
    def lookup_keys(self):
        """
        Lookup keys.

        Default implementation is all model fields that are defined in
        the Yaml block.
        """

        return (field.name for field in self.model._meta.get_fields())

    def lookup(self):
        """
        Generate the lookup
        """

        return {
            field: getattr(self, field)
            for field in self.lookup_keys
            if hasattr(self, field)
        }

    def get_object(self):
        """
        Get the object from the database.
        """
        return self.model.objects.get(**self.lookup())

    def __to_value__(self):
        obj = self.get_object()

        # update the object with any remaining keys
        for field in self.model._meta.get_fields():
            if hasattr(self, field.name):
                setattr(obj, field.name, getattr(self, field.name))

        return obj


# pylint:disable=abstract-method
class GetOrCreateForeignObject(GetForeignObject):
    """
    Get or create a foreign key reference for the provided parameters
    """

    def get_object(self):
        obj, _ = self.model.objects.get_or_create(**self.lookup())
        return obj
# pylint:enable=abstract-method


class Page(JSONSerializable, yaml.YAMLObject):
    """
    A reference to a page
    """

    yaml_tag = '!page'
    yaml_loader = yaml.SafeLoader

    def __to_json__(self):
        # pylint:disable=no-member
        url = PurePosixPath(self.url)

        if not url.is_absolute():
            raise ValueError("URL must be absolute")

        page = WagtailPage.objects.only('id').get(url_path=str(url) + '/')

        return page.id


class Image(FieldStorable, yaml.YAMLObject):
    """
    A reference to an image
    """

    yaml_tag = '!image'
    yaml_loader = yaml.SafeLoader

    file = None  # expected parameter

    @property
    def db_filename(self):
        """
        Filename that will be stored into the DB.

        This code is taken from Wagtail. We can't call into the Wagtail code
        because it will create unique filenames.
        """

        folder_name = 'original_images'
        filename = ('images/%s' % self.file).replace('/', '')
        filename = "".join((i if ord(i) < 128 else '_')
                           for i in unidecode(filename))

        while len(os.path.join(folder_name, filename)) >= 95:
            prefix, dot, extension = filename.rpartition('.')
            filename = prefix[:-1] + dot + extension

        return os.path.join(folder_name, filename)

    @transaction.atomic
    def __to_value__(self):
        try:
            obj = WagtailImage.objects.get(file=self.db_filename)

        except WagtailImage.DoesNotExist:
            print("Creating file %s..." % self.db_filename)
            with open('images/%s' % self.file, 'rb') as file_:
                file_ = File(file_)
                obj = WagtailImage(file=file_)
                # Need to save while the file is open
                obj.save()  # pylint:disable=no-member

        # copy the fields
        for field in obj._meta.get_fields():
            if field.name == 'file':
                continue
            elif hasattr(self, field.name):
                setattr(obj, field.name, getattr(self, field.name))

        obj.save()
