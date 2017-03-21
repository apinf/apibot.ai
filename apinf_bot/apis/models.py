# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models
from django_extensions.db.models import TimeStampedModel
from slugify import UniqueSlugify


class Swagger(TimeStampedModel):
    """
    A class to describe a Swagger file.
    """

    def __str__(self):
        return self.name

    swaggerfile = models.URLField(
        'Swagger file URL',
        max_length=200,
    )
    name = models.CharField(
        max_length=100,
    )
