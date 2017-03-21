# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from .models import (
    Swagger,
)


# class SwaggerAdmin(admin.ModelAdmin):
#     list_display = (
#         '__unicode__',
#         'created',
#         'name',
#     )
#     list_filter = (
#         'created',
#     )
#
#
# admin.site.register(Swagger, SwaggerAdmin)
admin.site.register(Swagger)
