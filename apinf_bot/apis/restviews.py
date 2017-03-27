# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import requests
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from swagger_parser import SwaggerParser

from .models import Swagger
from .serializers import (
    SwaggerSerializer,
    BotSerializer,
    BotResponseSerializer,
)


class SwaggerViewSet(ModelViewSet):
    """
    Retrieve, update or delete a Swagger instance.
    """
    queryset = Swagger.objects.all()
    serializer_class = SwaggerSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )


class BotView(APIView):
    """
    An endpoint that gives you the correct piece of information
    contained within a Swagger file.

    Only accepts POST requests.

    The endpoint is built for the api.ai platform:
    * https://docs.api.ai/docs/query#post-query
    * https://docs.api.ai/docs/webhook#webhook-example
    """
    def post(self, request, format=None):
        serializer = BotSerializer(data=request.data)
        output_data = {}

        # All the APIs
        queryset = Swagger.objects.all()

        if serializer.is_valid():
            # Check what type of data we need to return
            # List all APIs
            if serializer.validated_data['result']['parameters']['data'] == 'list':
                api_list = queryset.values_list('name', flat=True).order_by('name')
                output_data['displayText'] = ', '.join(api_list)

            # Information about specific API
            else:
                swagger = get_object_or_404(queryset, name=serializer.validated_data['result']['parameters']['api'])

                # Load the Swagger file from remote location
                swaggerfile = requests.get(swagger.swaggerfile)
                #  Parse the Swagger file
                parser = SwaggerParser(swagger_dict=swaggerfile.json())

                try:
                    json_specification = json.loads(parser.json_specification)
                    output_data['displayText'] = json_specification['info'][str(serializer.validated_data['result']['parameters']['data'])]
                    # # JSON specifications are all in a string that contains JSON
                    # # We need to slice up every piece of data
                    # # TODO:
                    # # We can probably make this generic
                    # if serializer.data == 'description':
                    #     json_specification = json.loads(parser.json_specification)
                    #     data['description'] = json_specification['info']['description']
                    # elif('title' in request.query_params['data']):
                    #     json_specification = json.loads(parser.json_specification)
                    #     data['title'] = json_specification['info']['title']
                    # elif('terms-of-service' in request.query_params['data']):
                    #     json_specification = json.loads(parser.json_specification)
                    #     data['terms-of-service'] = json_specification['info']['termsOfService']
                    # elif('contact' in request.query_params['data']):
                    #     json_specification = json.loads(parser.json_specification)
                    #     data['contact'] = json_specification['info']['contact']
                    # else:

                except:
                    output_data['displayText'] = 'Arrr! Here ye all be warned, for pirates are lurking...'

            output_data['speech'] = output_data['displayText']
            serializer = BotResponseSerializer(output_data)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
