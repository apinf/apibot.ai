# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    CharField,
    IntegerField,
    ListField,
    DictField,
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
    intent = CharField(allow_blank=True, max_length=100)
    data = CharField(allow_blank=True, max_length=100)
    method = CharField(allow_blank=True, max_length=10)


class BotResultSerializer(Serializer):
    parameters = BotParametersSerializer()
    # contexts = ListField(
    #     child=CharField(allow_blank=True, max_length=100),
    #     required=False,
    #     # allow_null=True,
    # )
    resolvedQuery = CharField(max_length=100)
    source = CharField(max_length=100)
    # score = CharField(max_length=100)
    # speech = CharField(max_length=100)
    # fulfillment = CharField(max_length=100)
    # actionIncomplete = CharField(max_length=100)
    action = CharField(allow_blank=True, max_length=100)
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


class ContextOutSerializer(Serializer):
    name = CharField(allow_blank=True, max_length=100)
    lifespan = IntegerField()
    parameters = DictField(
        child=CharField(),
    )


class BotResponseSerializer(Serializer):
    speech = CharField()
    displayText = CharField()
    data = DictField(
        child=CharField(allow_blank=True),
        required=False,
    )
    contextOut = ContextOutSerializer(required=False)
    source = CharField(default='apinf-bot')
