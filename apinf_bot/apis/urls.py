# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter

from .restviews import SwaggerViewSet


# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'^apis', SwaggerViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
]




#
# urlpatterns = [
#
#     url(
#         regex=r'^~swagger-detail/$',
#         view=SwaggerDetail.as_view(),
#         name='swagger-detail'
#     ),
# ]
#
# urlpatterns = format_suffix_patterns(urlpatterns)
#
#
# from django.conf.urls import url, include
# from snippets import views
# from rest_framework.routers import DefaultRouter
