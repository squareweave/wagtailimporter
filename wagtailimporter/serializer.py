"""
Objects for YAML serializer/deserializer
"""
import json
import logging
import os
from pathlib import PurePosixPath

import yaml
from unidecode import unidecode
from wagtail.contrib.settings.registry import registry
from wagtail.core.fields import StreamField
from wagtail.core.models import Page as WagtailPage
from wagtail.core.models import Site as WagtailSite
from wagtail.documents.models import Document as WagtailDocument
from wagtail.images.models import Image as WagtailImage

LOGGER = logging.getLogger(__name__)


def normalise(url):
    """Normalize URL paths by appending a trailing slash."""
    url = str(url)

    if not url.endswith('/'):
        url += '/'

    return url


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

    @classmethod
    def to_objects(cls, value):
        """Convert FieldStorables to objects."""
        if isinstance(value, cls):
            value = value.__to_value__()  # pylint:disable=no-member

        elif isinstance(value, list):
            value = [cls.to_objects(elem) for elem in value]

        elif isinstance(value, dict):
            value = {
                key: cls.to_objects(elem)
                for key, elem in value.items()
            }

        else:
            pass

        return value


class JSONEncoder(json.JSONEncoder):
    """
    Extension of the JSON encoder that knows how to encode the YAML objects
    """

    def default(self, o):  # pylint:disable=method-hidden
        if isinstance(o, JSONSerializable):
            return o.__to_json__()

        return super().default(o)


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
            field: FieldStorable.to_objects(getattr(self, field))
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
        lookup = self.lookup()

        # update the object with any remaining keys
        for field in self.model._meta.get_fields():

            # Skip fields used to find the instance
            if field.name in lookup:
                continue

            if hasattr(self, field.name):
                value = getattr(self, field.name)

                if isinstance(field, StreamField):
                    value = json.dumps(value, cls=JSONEncoder)
                else:
                    value = FieldStorable.to_objects(value)

                setattr(obj, field.name, value)

        return obj


# pylint:disable=abstract-method
class GetOrCreateForeignObject(GetForeignObject):
    """
    Get or create a foreign key reference for the provided parameters
    """

    def get_defaults(self):
        """
        Defaults to pass when creating an object.
        """
        defaults = {}

        for field in self.model._meta.get_fields():
            if hasattr(self, field.name):
                value = getattr(self, field.name)

                if isinstance(field, StreamField):
                    value = json.dumps(value, cls=JSONEncoder)
                else:
                    value = FieldStorable.to_objects(value)

                defaults[field.name] = value

        return defaults

    def get_object(self):
        obj, _ = self.model.objects.get_or_create(**self.lookup(),
                                                  defaults=self.get_defaults())
        return obj


class GetOrCreateClusterableForeignObject(GetForeignObject):
    """
    Get or create a foreign key reference for the provided parameters,
    assuming the parent of this object is a ClusterableModel.
    """

    def get_object(self):
        try:
            return super().get_object()
        except self.model.DoesNotExist:
            return self.model(**self.lookup())
# pylint:enable=abstract-method


class Page(FieldStorable, JSONSerializable, yaml.YAMLObject):
    """
    A reference to a page
    """

    yaml_tag = '!page'
    yaml_loader = yaml.SafeLoader

    def get_object(self):
        """
        Retrieve the page object.
        """
        # pylint:disable=no-member
        url = PurePosixPath(self.url)

        if not url.is_absolute():
            raise ValueError("URL must be absolute")

        return WagtailPage.objects.only('id').get(url_path=normalise(url))

    def __to_value__(self):
        return self.get_object()

    def __to_json__(self):
        return self.get_object().id


class Image(JSONSerializable, GetOrCreateForeignObject):
    """
    A reference to an image
    """

    yaml_tag = '!image'
    yaml_loader = yaml.SafeLoader
    model = WagtailImage

    file = None  # expected parameter

    def lookup(self):
        return {'file': self.db_filename}

    @property
    def db_filename(self):
        """
        Filename that will be stored into the DB.

        This code is taken from Wagtail. We can't call into the Wagtail code
        because it will create unique filenames.
        """

        folder_name = 'original_images'
        filename = 'images/%s' % self.file.replace('/', '-')
        filename = "".join((i if ord(i) < 128 else '_')
                           for i in unidecode(filename))

        max_length = 95
        path = os.path.join(folder_name, filename)
        if len(path) > max_length:
            prefix, extension = os.path.splitext(filename)
            path = prefix[:max_length - len(path)] + extension

        return path

    def get_object(self):
        try:
            return self.model.objects.get(**self.lookup())
        except self.model.DoesNotExist:
            LOGGER.info("Creating file %s...", self.db_filename)

            storage = self.model._meta.get_field('file').storage
            filename = self.db_filename
            if not storage.exists(filename):
                with open('images/%s' % self.file, 'rb') as source:
                    filename = storage.save(filename, source)

            image = self.model(file=filename)
            image.save()  # pylint:disable=no-member
            return image

    def __to_json__(self):
        return self.__to_value__().id


class Document(JSONSerializable, GetOrCreateForeignObject):
    """
    A reference to a document
    """

    yaml_tag = '!document'
    yaml_loader = yaml.SafeLoader
    model = WagtailDocument

    # expected parameters
    file = None
    title = ''

    def lookup(self):
        return {'file': self.db_filename}

    @property
    def db_filename(self):
        """Generate a filename to store in the database for this Document."""
        folder_name = 'documents'
        # wagtail code doesn't appear to manipulate document filenames like it
        # does for images!
        path = os.path.join(folder_name, self.file)
        return path

    def get_object(self):
        try:
            return self.model.objects.get(**self.lookup())
        except self.model.DoesNotExist:
            LOGGER.info("Creating file %s...", self.db_filename)

            storage = self.model._meta.get_field('file').storage
            filename = self.db_filename
            if not storage.exists(filename):
                with open('documents/%s' % self.file, 'rb') as source:
                    filename = storage.save(filename, source)

            doc = self.model(file=filename, title=self.title)
            doc.save()  # pylint:disable=no-member
            return doc

    def __to_json__(self):
        return self.__to_value__().id


class Site(GetOrCreateForeignObject):
    """
    A Wagtail site.

    !site
        hostname: localhost
        site_name: My Site
        root_page: !page
            url: /my-site
        is_default_site: true
    """

    yaml_tag = '!site'
    model = WagtailSite
    lookup_keys = ('hostname',)


# Make a getter for each registered Wagtail setting, lookup using its app.model
# lowercase dotted model name.
for SomeSetting in registry:
    type(SomeSetting.__name__, (GetOrCreateForeignObject,), {
        'yaml_tag': '!{}'.format(SomeSetting._meta.label_lower),
        'model': SomeSetting,
        'lookup_keys': ('site',)
    })
