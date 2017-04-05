# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pprint

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from swagger_spec_validator import validate_spec_url

from .models import Swagger
from .serializers import (
    SwaggerSerializer,
    BotSerializer,
    BotResponseSerializer,
)
from .lists import (
    info_fields,
    general_data,
    swagger_fields,
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
    def get_parser(self, parameters, contexts):
        """
        We might be getting the API name from paramaters straight or
        from passed context
        """
        if 'api' in parameters:
            api = parameters['api']
        elif contexts and 'api' in contexts[0]['parameters']:
            api = contexts[0]['parameters']['api']
        swagger = Swagger.objects.get(name__icontains=api)
        return swagger.parse_swaggerfile()

    def post(self, request, format=None):
        generic_error_msg = _('Arrr! Here ye all be warned, for pirates are lurking...')
        not_existing_msg = _('This information is not defined in the Swagger file. Sorry!')
        not_defined_msg = _('This data is not part of the OpenAPI specifications: https://github.com/OAI/OpenAPI-Specification')
        no_api_msg = _('We do not have information about this API. Feel free to add it yourself!')

        serializer = BotSerializer(data=request.data)
        output_data = {}

        if serializer.is_valid():
            # All the APIs
            queryset = Swagger.objects.all()
            parameters = serializer.validated_data['result']['parameters']
            contexts = serializer.validated_data['result']['contexts']
            metadata = serializer.validated_data['result']['metadata']
            action = serializer.validated_data['result']['action']

            # Check what type of data we need to return
            # List all APIs
            ###############
            if  action == 'api.list':
                api_list = queryset.values_list('name', flat=True).order_by('name')
                output_data['displayText'] = _('We have these APIs:\n{0}\n Just tell me if you want to add some more.').format('\n'.join(api_list))

            # Add a new API
            ###############
            elif action == 'api.create':
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
                        # Validate the URL that it is a Swagger 2.0 file
                        try:
                            # Validate the JSON file. Will throw an exception
                            # if the file is not valid
                            validate_spec_url(parameters['url'])
                            # Create new API
                            Swagger.objects.create(
                                name=parameters['api'],
                                swaggerfile=parameters['url'],
                            )
                            output_data['displayText'] = _('New API added, thanks!')
                        except Exception:
                            output_data['displayText'] = _('The URL does not point to a valid Swagger 2.0 file.')
                except KeyError:
                    output_data['displayText'] = _('I need a name and URL pointing to a OpenAPI json specification in order to create a new API.')

            # Information about specific API
            ################################
            elif action == 'api.info':
                try:
                    parser = self.get_parser(parameters, contexts)
                    # Do we have a request for generic information of this API?
                    if parameters['data'] in info_fields:
                        try:
                            output_data['displayText'] = parser.specification['info'][parameters['data']]
                        except:
                            output_data['displayText'] = not_existing_msg

                    # Do we have Swagger object fields?
                    elif parameters['data'] in swagger_fields:
                        try:
                            output_data['displayText'] = parser.specification[parameters['data']]
                        except:
                            output_data['displayText'] = not_existing_msg

                    # Some general data about the API
                    elif parameters['data'] in general_data:
                        # List all the paths
                        if parameters['data'] == 'paths':
                            paths = parser.paths.keys()
                            output_data['displayText'] = '\n'.join(paths)

                        # List all the operations
                        elif parameters['data'] == 'operations':
                            operations = parser.operation.keys()
                            output_data['displayText'] = '\n'.join(operations)

                        # List all the objects
                        elif parameters['data'] == 'definitions':
                            definitions = parser.definitions_example.keys()
                            output_data['displayText'] = '\n'.join(definitions)

                    # No idea what they want...
                    # TODO: start logging these so we can analyze
                    else:
                        output_data['displayText'] = not_defined_msg

                except ObjectDoesNotExist:
                    output_data['displayText'] = no_api_msg
                except Exception:
                    output_data['displayText'] = generic_error_msg

            # Object definitions for specific API
            #####################################
            elif action == 'api.object-definition':
                try:
                    parser = self.get_parser(parameters, contexts)
                    try:
                        output_data['displayText'] = pprint.pformat(parser.definitions_example[parameters['object']], indent=4, width=1)
                    except KeyError:
                        output_data['displayText'] = not_defined_msg

                except ObjectDoesNotExist:
                    output_data['displayText'] = no_api_msg

            # Operation definitions for specific API
            ########################################
            elif action == 'api.operation':
                try:
                    parser = self.get_parser(parameters, contexts)
                    try:
                        output_data['displayText'] = pprint.pformat(parser.operation[parameters['operation']], indent=4, width=1)
                    except KeyError:
                        output_data['displayText'] = not_defined_msg

                except ObjectDoesNotExist:
                    output_data['displayText'] = no_api_msg

            # Path info for specific API
            ############################
            elif action == 'api.path':
                try:
                    parser = self.get_parser(parameters, contexts)
                    try:
                        output_data['displayText'] = pprint.pformat(parser.paths[parameters['path']], indent=4, width=1)
                    except KeyError:
                        output_data['displayText'] = not_defined_msg

                except ObjectDoesNotExist:
                    output_data['displayText'] = no_api_msg

            elif metadata['intentName'] == 'api-endpoint':
                try:
                    swagger = queryset.get(name__icontains=parameters['api'])
                    #  Parse the Swagger file
                    parser = swagger.parse_swaggerfile()
                    pass

                except ObjectDoesNotExist:
                    output_data['displayText'] = no_api_msg

            # We have no idea what this intent is...
            else:
                output_data['displayText'] = not_defined_msg

            # For now duplicate the display text and speech
            output_data['speech'] = output_data['displayText']
            serializer = BotResponseSerializer(output_data)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
