# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import requests
from django.utils.translation import ugettext_lazy as _
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

        if serializer.is_valid():
            # All the APIs
            queryset = Swagger.objects.all()
            parameters = serializer.validated_data['result']['parameters']

            # Check what type of data we need to return
            # List all APIs
            if  parameters['data'] == 'list':
                api_list = queryset.values_list('name', flat=True).order_by('name')
                output_data['displayText'] = _('We have these APIs:\n "{0}"\n Just tell me if you want to add some more.').format('\n'.join(api_list))

            # Add a new API
            elif parameters['data'] == 'create':
                # Check for existing APIs first
                try:
                    # API with same name exists
                    if(queryset.filter(name=parameters['api'])):
                        output_data['displayText'] = _('An API with this name already exists!')
                    # API with same URL exists
                    elif(queryset.filter(swaggerfile=parameters['url'])):
                        output_data['displayText'] = _('An API pointing to this URL already exists!')
                    # Create new API
                    else:
                        Swagger.objects.create(
                            name=parameters['api'],
                            swaggerfile=parameters['url'],
                        )
                        output_data['displayText'] = _('New API added, thanks!')
                except KeyError:
                    output_data['displayText'] = _('I need a name and URL pointing to a OpenAPI json specification in order to create a new API.')

            # Information about specific API
            elif parameters['api']:
                swagger = get_object_or_404(queryset, name=parameters['api'])
                # Load the Swagger file from remote location
                swaggerfile = requests.get(swagger.swaggerfile)
                #  Parse the Swagger file
                parser = SwaggerParser(swagger_dict=swaggerfile.json())

                # Do we have a request for generic information of this API?
                if parameters['data'] in ('contact', 'description', 'version', 'title', 'termsOfService', 'license'):
                    try:
                        json_specification = json.loads(parser.json_specification)
                        output_data['displayText'] = json_specification['info'][str(parameters['data'])]
                    except:
                        output_data['displayText'] = 'Arrr! Here ye all be warned, for pirates are lurking...'
                if parameters['data'] in ('host', 'basePath', ):
                    import pdb; pdb.set_trace()
                    pass

            output_data['speech'] = output_data['displayText']
            serializer = BotResponseSerializer(output_data)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
