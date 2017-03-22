# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    CharField,
    ListField,
)

from .models import Swagger


class SwaggerSerializer(ModelSerializer):
    """
    A serializer to deal with specified Swagger-defined endpoints.
    """

    class Meta:
        model = Swagger
        fields = (
            'id',
            'swaggerfile',
            'name',
        )
        read_only_fields = (
            'id',
        )


class BotParametersSerializer(Serializer):
    api = CharField(max_length=100)
    data = ListField(
        child=CharField(max_length=100),
    )


class BotResultSerializer(Serializer):
    parameters = BotParametersSerializer()
    contexts = ListField(
        child=CharField(max_length=100),
    )
    resolvedQuery = CharField(max_length=100)
    source = CharField(max_length=100)
    # score = CharField(max_length=100)
    # speech = CharField(max_length=100)
    # fulfillment = CharField(max_length=100)
    # actionIncomplete = CharField(max_length=100)
    action = CharField(max_length=100)
    # metadata = CharField(max_length=100)


class BotSerializer(Serializer):
    """
    A serializer to deal with the POST body coming
    from the bot.
    """
    lang = CharField(max_length=10)
    timestamp = CharField(max_length=100)
    sessionId = CharField(max_length=100)
    result = BotResultSerializer()
