"""
Objects for YAML serializer/deserializer
"""

import json
from pathlib import PurePosixPath

import yaml

from wagtail.wagtailcore.models import Page as WagtailPage


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

    def lookup(self):
        """
        Generate the lookup
        """

        return {
            field.name: getattr(self, field.name)
            for field in self.model._meta.get_fields()
            if hasattr(self, field.name)
        }

    def __to_value__(self):
        return self.model.objects.get(**self.lookup())


# pylint:disable=abstract-method
class GetOrCreateForeignObject(GetForeignObject):
    """
    Get or create a foreign key reference for the provided parameters
    """

    def __to_value__(self):
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
