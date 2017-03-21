# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

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
        print(request.query_params)
        data = serializer.data

        try:
            if('description' in request.query_params['data']):
                data = {'description': 'foobar', }
        except:
            pass


        return Response(data)
