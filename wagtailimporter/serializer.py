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
from django.db import models, transaction
from wagtail.wagtailcore.models import Page as WagtailPage
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailimages.models import Image as WagtailImage

LOGGER = logging.getLogger(__name__)


class YAMLSerializableMetaclass(yaml.YAMLObjectMetaclass):
    """
    Yaml registration metaclass
    """
    def __init__(cls, name, bases, kwargs):
        super().__init__(name, bases, kwargs)
        model = kwargs.get('model')

        if model is not None:
            cls.yaml_dumper.add_representer(model, cls.__to_yaml__)


class YAMLSerializable(yaml.YAMLObject, metaclass=YAMLSerializableMetaclass):
    """
    Base Yaml object
    """

    yaml_loader = yaml.SafeLoader

    @classmethod
    def __to_yaml__(cls, dumper, data):
        obj = cls.__from_value__(data)
        return obj.to_yaml(dumper, obj)

    @classmethod
    def __from_value__(cls, obj):
        """Convert a real ORM object into a YAMLSerializable."""
        raise NotImplementedError()


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

    def default(self, obj):  # pylint:disable=method-hidden
        if isinstance(obj, JSONSerializable):
            return obj.__to_json__()

        return super().default(obj)


class GetForeignObject(FieldStorable, YAMLSerializable):
    """
    Get a foreign key reference for the provided parameters
    """

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

        # update the object with any remaining keys
        for field in self.model._meta.get_fields():
            if hasattr(self, field.name):
                value = getattr(self, field.name)

                if isinstance(field, StreamField):
                    value = json.dumps(value, cls=JSONEncoder)
                else:
                    value = FieldStorable.to_objects(value)

                setattr(obj, field.name, value)

        return obj

    @classmethod
    def __from_value__(cls, obj):
        output = cls()

        for field in obj._meta.get_fields():
            if field.auto_created:
                continue

            value = getattr(obj, field.name)

            if value is None or value == field.default or value == '':
                continue

            elif isinstance(field, models.FileField):
                value = value.name  # FIXME: broken

            elif isinstance(value, models.Manager):
                continue

            elif isinstance(value, models.Model):
                continue

            setattr(output, field.name, value)

        return output


# pylint:disable=abstract-method
class GetOrCreateForeignObject(GetForeignObject):
    """
    Get or create a foreign key reference for the provided parameters
    """

    def get_object(self):
        obj, _ = self.model.objects.get_or_create(**self.lookup())
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

    def get_object(self):
        """
        Retrieve the page object.
        """
        # pylint:disable=no-member
        url = PurePosixPath(self.url)

        if not url.is_absolute():
            raise ValueError("URL must be absolute")

        return WagtailPage.objects.only('id').get(url_path=str(url) + '/')

    def __to_value__(self):
        return self.get_object()

    def __to_json__(self):
        return self.get_object().id


class Image(FieldStorable, JSONSerializable, YAMLSerializable):
    """
    A reference to an image
    """

    model = WagtailImage
    yaml_tag = '!image'

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
    def get_object(self):
        """
        Retrieve the image object.
        """

        try:
            obj = self.model.objects.only('id').get(file=self.db_filename)

        except self.model.DoesNotExist:
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

        obj.save()  # pylint:disable=no-member

        return obj

    def __to_value__(self):
        return self.get_object()

    def __to_json__(self):
        return self.get_object().id

    @classmethod
    def __from_value__(cls, obj):
        output = cls()

        for field in obj._meta.get_fields():
            if field.auto_created:
                continue

            value = getattr(obj, field.name)

            if value is None or value == field.default or value == '':
                continue

            elif isinstance(field, models.FileField):
                value = value.name  # FIXME: broken

            elif isinstance(value, models.Manager):
                continue

            elif isinstance(value, models.Model):
                continue

            setattr(output, field.name, value)

        return output
