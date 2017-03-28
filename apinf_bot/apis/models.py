# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel


class Swagger(TimeStampedModel):
    """
    A class to describe a Swagger file.
    """

    def __str__(self):
        return self.name

    swaggerfile = models.URLField(
        _('Swagger file URL'),
        max_length=200,
    )
    name = models.CharField(
        max_length=100,
    )
