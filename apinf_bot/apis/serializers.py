# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    CharField,
    IntegerField,
    URLField,
    BooleanField,
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


# Incoming requests
class BotParametersSerializer(Serializer):
    api = CharField(required=False, allow_blank=True, max_length=100)
    api = CharField(required=False, allow_blank=True, max_length=100)
    object = CharField(required=False, allow_blank=True, max_length=100)
    operation = CharField(required=False, allow_blank=True, max_length=100)
    path = CharField(required=False, allow_blank=True, max_length=255)
    data = CharField(required=False, allow_blank=True, max_length=100)
    method = CharField(required=False, allow_blank=True, max_length=10)
    endpoint = CharField(required=False, allow_blank=True, max_length=100)
    url = URLField(required=False, allow_blank=True, max_length=255)


class BotMetadataSerializer(Serializer):
    intentId = CharField(required=False, allow_blank=True, max_length=100)
    webhookUsed = BooleanField(required=False)
    webhookForSlotFillingUsed = BooleanField(required=False)
    intentName = CharField(required=False, allow_blank=True, max_length=100)


class BotContextsSerializer(Serializer):
    name = CharField(required=False, allow_blank=True, max_length=100)
    parameters = BotParametersSerializer()
    lifespan = IntegerField(required=False)


class BotResultSerializer(Serializer):
    parameters = BotParametersSerializer()
    contexts = ListField(
        child=BotContextsSerializer(),
        required=False,
    )
    resolvedQuery = CharField(max_length=1000)
    source = CharField(max_length=100)
    # score = CharField(max_length=100)
    # speech = CharField(max_length=100)
    # fulfillment = CharField(max_length=100)
    # actionIncomplete = CharField(max_length=100)
    action = CharField(required=False, allow_blank=True, max_length=100)
    metadata = BotMetadataSerializer(required=False)


class BotSerializer(Serializer):
    """
    A serializer to deal with the POST body coming
    from the bot.
    """
    lang = CharField(max_length=10)
    timestamp = CharField(max_length=100)
    sessionId = CharField(max_length=100)
    result = BotResultSerializer()


# Outgoing requests
class ContextOutSerializer(Serializer):
    name = CharField(required=False, max_length=100)
    lifespan = IntegerField()
    parameters = DictField(
        child=CharField(),
    )


# Facebook specific data response
class FBQuickRepliesSerializer(Serializer):
    content_type = CharField(required=False, max_length=100, default='text')
    title = CharField(required=False, max_length=255)
    payload = CharField(required=False, max_length=255)


class FBQuickRepliesListSerializer(Serializer):
    text = CharField(required=False)
    quick_replies = ListField(
        child=FBQuickRepliesSerializer(),
        required=False,
    )


# Slack specific data response
# https://api.slack.com/docs/message-buttons
class SLActionsSerializer(Serializer):
    name = CharField(required=False)
    text = CharField(required=False)
    type = CharField(required=False, default='button')
    value = CharField(required=False)



class SLAttachmentsSerializer(Serializer):
    text = CharField(required=False)
    fallback = CharField(required=False)
    callback_id = CharField(required=False)
    color = CharField(required=False)
    attachment_type = CharField(required=False, default='default')
    actions = ListField(
        child=SLActionsSerializer(),
        required=False,
    )


class SLAttachmentsListSerializer(Serializer):
    text = CharField(required=False)
    attachments = ListField(
        child=SLAttachmentsSerializer(),
        required=False,
    )


class DataSerializer(Serializer):
    slack = SLAttachmentsListSerializer(required=False)
    facebook = FBQuickRepliesListSerializer(required=False)

class BotResponseSerializer(Serializer):
    speech = CharField()
    displayText = CharField()
    data = DataSerializer(required=False)
    contextOut = ContextOutSerializer(required=False)
    source = CharField(default='apinf-bot')
