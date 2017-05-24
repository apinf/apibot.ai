# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel


class Feedback(TimeStampedModel):
    """
    Feedback that a user provides through the bot.
    """

    # def __str__(self):
    #     return self.name

    feedback = models.TextField(
        blank=True,
        null=True,
    )

    username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
