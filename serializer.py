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


class JSONEncoder(json.JSONEncoder):
    """
    Extension of the JSON encoder that knows how to encode the YAML objects
    """

    def default(self, obj):  # pylint:disable=method-hidden
        if isinstance(obj, JSONSerializable):
            return obj.__to_json__()

        return super().default(obj)


class Page(JSONSerializable, yaml.YAMLObject):
    """
    Ability to deserialise a page
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
