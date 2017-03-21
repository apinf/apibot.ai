# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import requests
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from swagger_parser import SwaggerParser

from .models import Swagger
from .serializers import SwaggerSerializer


class SwaggerViewSet(ModelViewSet):
    """
    Retrieve, update or delete a Swagger instance.
    """
    queryset = Swagger.objects.all()
    serializer_class = SwaggerSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def retrieve(self, request, pk=None):
        queryset = Swagger.objects.all()
        swagger = get_object_or_404(queryset, pk=pk)
        serializer = SwaggerSerializer(swagger)

        # Load the Swagger file from remote location
        swaggerfile = requests.get(swagger.swaggerfile)
        #  Parse the Swagger file
        parser = SwaggerParser(swagger_dict=swaggerfile.json())

        data = {}
        try:
            # JSON specifications are all in a string that contains JSON
            # We need to slice up every piece of data
            # TODO:
            # We can probably make this generic
            if('description' in request.query_params['data']):
                json_specification = json.loads(parser.json_specification)
                data['description'] = json_specification['info']['description']
            if('title' in request.query_params['data']):
                json_specification = json.loads(parser.json_specification)
                data['title'] = json_specification['info']['title']
            if('terms-of-service' in request.query_params['data']):
                json_specification = json.loads(parser.json_specification)
                data['terms-of-service'] = json_specification['info']['termsOfService']
            if('contact' in request.query_params['data']):
                json_specification = json.loads(parser.json_specification)
                data['contact'] = json_specification['info']['contact']
        except:
            data = serializer.data



        return Response(data)
