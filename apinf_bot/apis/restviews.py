# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

# TODO
# v Output formatting of dictionaries
# v Descriptions have words split over lines
# v when no operationId available, button does not work
# - create new API fails
# - Split code into functions to make it more readable
# - Security definitions
import pprint
import re

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import URLValidator

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
    FBQuickRepliesSerializer,
    FBQuickRepliesListSerializer,
    DataSerializer,
    SLActionsSerializer,
    SLAttachmentsSerializer,
    SLAttachmentsListSerializer,
)
from .lists import (
    info_fields,
    general_data,
    swagger_fields,
)
from ..utils.utils import url_is_alive


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
    def get_api(self, parameters, contexts):
        if 'api' in parameters:
            return parameters['api']
        elif contexts:
            for context in contexts:
                if 'api' in context['parameters']:
                    return context['parameters']['api']
        return None

    def get_parser(self, api):
        """
        We might be getting the API name from paramaters straight or
        from passed context
        """
        try:
            return Swagger.objects.get(name__icontains=api).parse_swaggerfile()
        except Exception:
            return None

    def post(self, request, format=None):
        # Some docs:
        # Slack
        # Basic formatting: https://api.slack.com/docs/message-formatting
        generic_error_msg = _('Something went wrong here... I will tell the developers and hopefully they will manage to fix this.')
        not_existing_msg = _('This information is not defined in the Swagger file. Sorry!')
        not_defined_msg = _('This data is not part of the OpenAPI specifications: https://github.com/OAI/OpenAPI-Specification')
        no_api_msg = _('We do not have information about this API. Feel free to add it yourself!')

        serializer = BotSerializer(data=request.data)
        output_data = {}

        if serializer.is_valid():
            # All the APIs
            queryset = Swagger.objects.all()

            # Parse some of the input from api.ai
            parameters = serializer.validated_data['result']['parameters']
            contexts = serializer.validated_data['result']['contexts']
            metadata = serializer.validated_data['result']['metadata']
            action = serializer.validated_data['result']['action']

            # Check what type of data we need to return

            # List all APIs
            ###############
            if  action == 'api.list':
                api_list = queryset.values_list('name', flat=True).order_by('name')

                # Define buttons for Slack
                actions = []

                for api in api_list:
                    actions.append({
                            'name': api,
                            'text': api,
                            'value': _('Use {0}').format(api),
                        }
                    )

                attachments = {
                    'text': _('Which API you want to know more about? Here are top APIs:'),
                    'fallback': generic_error_msg,
                    'callback_id': 'api_list',
                    'actions': actions,
                }
                attachments_list = {
                    'text': _('We have these APIs:\n{0}\nIf you want to know more about a certain API, just tell me you want to *use* that one.\nYou can also *create* a new API if you have a URL to a valid Swagger file.').format('\n'.join(api_list)),
                    'attachments': [attachments, ],
                }
                data_response = {
                    'slack': attachments_list,
                }

                output_data['data'] = data_response

                output_data['displayText'] = _('We have these APIs:\n{0}\nIf you want to know more about a certain API, just tell me you want to *use* that one.\nYou can also *create* a new API if you have a URL to a valid Swagger file.').format('\n'.join(api_list))

            # Add a new API
            ###############
            elif action == 'api.create':
                try:
                    # Bugfix
                    # we lose the http(s):// from Slack input
                    # verify and add it if necessary
                    url = ''
                    if url_is_alive(parameters['url']):
                        url = parameters['url']
                    elif url_is_alive('http://' + parameters['url']):
                        url = 'http://' + parameters['url']
                    elif url_is_alive('https://' + parameters['url']):
                        url = 'https://' + parameters['url']
                    else:
                        output_data['displayText'] = _('This is an invalid URL!')

                    # # Do we have a valid URL?
                    # validate_url = URLValidator()
                    # try:
                    #     validate_url(parameters['url'])
                    #     url = parameters['url']
                    # # The http got stripped out
                    # except ValidationError:
                    #     try:
                    #         validate_url('http://{0}'.format(parameters['url']))
                    #         url = 'http://{0}'.format(parameters['url'])
                    #     except ValidationError:
                    #         output_data['displayText'] = _('This is an invalid URL!')

                    if(url):
                        # API with same name exists
                        if(queryset.filter(name=parameters['api'])):
                            output_data['displayText'] = _('An API with this name already exists!')
                        # API with same URL exists
                        elif(queryset.filter(swaggerfile=url)):
                            output_data['displayText'] = _('An API pointing to this URL already exists!')
                        # Create new API
                        else:
                            # Validate the URL that it is a Swagger 2.0 file
                            try:
                                # Validate the JSON file. Will throw an exception
                                # if the file is not valid
                                validate_spec_url(url)
                                # Create new API
                                Swagger.objects.create(
                                    name=parameters['api'],
                                    swaggerfile=url,
                                )
                                output_data['displayText'] = _('New API added, thanks!')
                            except:
                                output_data['displayText'] = _('This is not a valid Swagger 2.0 file.')
                except KeyError:
                    output_data['displayText'] = _('I need a name and URL pointing to a OpenAPI json specification in order to create a new API.')

            # Information about specific API
            ################################
            elif action == 'api.info':
                try:
                    api = self.get_api(parameters, contexts)
                    parser = self.get_parser(api)
                    # Do we have a request for generic information of this API?
                    if parameters['data'] in info_fields:
                        try:
                            output_data['displayText'] = _('Here is the *{0}* you asked for *{1}*:\n{2}').format(
                                parameters['data'],
                                api,
                                parser.specification['info'][parameters['data']],
                            )
                        except:
                            output_data['displayText'] = not_existing_msg

                    # Do we have Swagger object fields?
                    elif parameters['data'] in swagger_fields:
                        try:
                            output_data['displayText'] = _('Here is the *{0}* you asked for *{1}*:\n{2}').format(
                                parameters['data'],
                                api,
                                parser.specification[parameters['data']]
                            )
                        except:
                            output_data['displayText'] = not_existing_msg

                    # Some general data about the API
                    elif parameters['data'] in general_data:
                        # List all the paths
                        # TODO
                        # Add buttons
                        if parameters['data'] == 'paths':
                            paths = parser.paths.keys()
                            if(paths):
                                # Define buttons for Slack
                                actions = []

                                for path in paths:
                                    actions.append({
                                            'name': path,
                                            'text': path,
                                            'value': _('Explain path {0}').format(path),
                                        }
                                    )

                                attachments = {
                                    'text': _('Which path you want to know more about? Here are the top paths:'),
                                    'fallback': generic_error_msg,
                                    'callback_id': 'paths',
                                    'actions': actions,
                                }
                                attachments_list = {
                                    'text': _('Here is a *list of paths* defined:\n{0}').format('\n'.join(paths)),
                                    'attachments': [attachments, ],
                                }
                                data_response = {
                                    'slack': attachments_list,
                                }

                                output_data['data'] = data_response

                                output_data['displayText'] = _('Here is the *{0}* you asked for *{1}*:\n{2}').format(
                                    parameters['data'],
                                    api,
                                    '\n'.join(paths)
                                )
                            else:
                                output_data['displayText'] = _('There are no paths defined in this OpenAPI specification.')

                        # List all the operations
                        elif parameters['data'] == 'operations':
                            operations = parser.operation.keys()
                            if(operations):
                                # Define buttons for Slack
                                actions = []

                                for operation in operations:
                                    actions.append({
                                            'name': operation,
                                            'text': operation,
                                            'value': _('Explain operation {0}').format(operation),
                                        }
                                    )

                                attachments = {
                                    'text': _('Which operation you want to know more about? Here are the top operations:'),
                                    'fallback': generic_error_msg,
                                    'callback_id': 'operations',
                                    'actions': actions,
                                }
                                attachments_list = {
                                    'text': _('Here is a *list of operations* defined:\n{0}').format('\n'.join(operations)),
                                    'attachments': [attachments, ],
                                }
                                data_response = {
                                    'slack': attachments_list,
                                }

                                output_data['data'] = data_response

                                output_data['displayText'] = _('Here is the *{0}* you asked for *{1}*:\n{2}').format(
                                    parameters['data'],
                                    api,
                                    '\n'.join(operations)
                                )
                            else:
                                output_data['displayText'] = _('There are no operations defined in this OpenAPI specification.')

                        # List all the objects
                        elif parameters['data'] == 'definitions':
                            definitions = parser.specification['definitions'].keys()
                            if(definitions):
                                # Define buttons for Slack
                                actions = []

                                for definition in definitions:
                                    actions.append({
                                            'name': definition,
                                            'text': definition,
                                            'value': _('Explain object {0}').format(definition),
                                        }
                                    )

                                attachments = {
                                    'text': _('Which object you want to know more about? Here are top objects:'),
                                    'fallback': generic_error_msg,
                                    'callback_id': 'object_definitions',
                                    'actions': actions,
                                }
                                attachments_list = {
                                    'text': _('Here is a *list of objects* defined:\n{0}').format('\n'.join(definitions)),
                                    'attachments': [attachments, ],
                                }
                                data_response = {
                                    'slack': attachments_list,
                                }

                                output_data['data'] = data_response

                                # And display text
                                output_data['displayText'] = '\n'.join(definitions)
                            else:
                                # And display text
                                output_data['displayText'] = _('No objects are defined in this OpenAPI specification.')

                    # No idea what they want...
                    # TODO: start logging these so we can analyze
                    else:
                        output_data['displayText'] = not_defined_msg

                except ObjectDoesNotExist:
                    output_data['displayText'] = no_api_msg
                except Exception as e:
                    output_data['displayText'] = str(e)

            # Object definitions for specific API
            #####################################
            elif action == 'api.object-definition':
                try:
                    # TODO
                    # Give an example can be added explicitly
                    api = self.get_api(parameters, contexts)
                    parser = self.get_parser(api)
                    # Sometimes the keys are stored in lower or titlecase.
                    # We deal with that.
                    if(parameters['object'] in parser.specification['definitions']):
                        definition = parser.specification['definitions'][parameters['object']]
                    elif(parameters['object'].lower() in parser.specification['definitions']):
                        definition = parser.specification['definitions'][parameters['object'].lower()]
                    else:
                        definition = parser.specification['definitions'][parameters['object'].title()]

                    # Are there linked operations to this object?
                    # TODO
                    # Follow-up on https://github.com/OAI/OpenAPI-Specification/issues/1097
                    # Now comes a dirty and messy method filled with assumptions
                    # But it's the best we can do so far

                    # 1. Check for schema references to the object
                    # 1.1 parameters
                    # (Pdb) parser.paths['/v2/pet']['put']['parameters']['body']['schema']['$ref']
                    # parser.paths[path][method]['parameters']['body']['schema']['$ref']
                    # Loop through every path, method
                    # 1.2 Response
                    # (Pdb) parser.paths['/v2/pet/{petId}']['get']['responses']['200']['schema']['$ref']
                    # parser.paths[path][method]['responses'][status-code]['schema']['$ref']
                    # Loop through every path, method, status-code
                    # result: '#/definitions/<object>' - regex
                    # 2. Check for tags using the same name
                    # (Pdb) parser.operation['getInventory'][2]
                    # parser.operation[operation][2]
                    # Loop through operations
                    # 'store'
                    # 3. Check for paths containing the same name - regex
                    # 4. Check for operations containing the same name - regex

                    operations = []

                    for path in parser.specification['paths']:
                        for method in parser.specification['paths'][path]:
                            # Sometimes we don't have the operationID defined
                            # Show method and path instead
                            if('operationId' in parser.specification['paths'][path][method]):
                                operation = {
                                    'type': 'operation',
                                    'value': parser.specification['paths'][path][method]['operationId'],
                                }
                            else:
                                operation = {
                                    'type': 'path',
                                    'value': _('{0} {1}').format(method.upper(), path, ),
                                }

                            # Do we have tags referencing the object?
                            if('tags' in parser.specification['paths'][path][method]):
                                if(parameters['object'].lower() in [tag.lower() for tag in parser.specification['paths'][path][method]['tags']]):
                                    operation['path'] = path
                                    operation['method'] = method
                                    operations.append(operation)
                                    break

                            # Do we have the name of the object in the path somewhere?
                            if(parameters['object'].lower() in path):
                                operation['path'] = path
                                operation['method'] = method
                                operations.append(operation)
                                break

                            # Do we have the name of the object in the operation name somewhere?
                            if(parameters['object'].lower() in operation):
                                operation['path'] = path
                                operation['method'] = method
                                operations.append(operation)
                                break

                            # Do we have input parameters referencing the object? e.g. PUT or POST methods
                            if('parameters' in parser.specification['paths'][path][method]):
                                for parameter in parser.specification['paths'][path][method]['parameters']:
                                    # Regex the object out
                                    try:
                                        match = re.match(r'#/definitions/(\w+)', parameter['schema']['$ref'])
                                        # Does the object match the input from user?
                                        if(match and match.group(1).lower() == parameters['object'].lower()):
                                            operation['path'] = path
                                            operation['method'] = method
                                            operations.append(operation)
                                            break
                                    except Exception:
                                        pass

                            # Do we have responses referencing the object? e.g. GET methods
                            if('responses' in parser.specification['paths'][path][method]):
                                try:
                                    for status_code in parser.specification['paths'][path][method]['responses']:
                                        if('schema' in parser.specification['paths'][path][method]['responses'][status_code]):
                                            # In case of a list of objects
                                            if('items' in parser.specification['paths'][path][method]['responses'][status_code]['schema']):
                                                match = re.match(r'#/definitions/(\w+)', parser.specification['paths'][path][method]['responses'][status_code]['schema']['items']['$ref'])
                                                # Does the object match the input from user?
                                                if(match and match.group(1).lower() == parameters['object'].lower()):
                                                    operation['path'] = path
                                                    operation['method'] = method
                                                    operations.append(operation)
                                                    break
                                            # In case of a single item
                                            else:
                                                match = re.match(r'#/definitions/(\w+)', parser.specification['paths'][path][method]['responses'][status_code]['schema']['$ref'])
                                                # Does the object match the input from user?
                                                if(match and match.group(1).lower() == parameters['object'].lower()):
                                                    operation['path'] = path
                                                    operation['method'] = method
                                                    operations.append(operation)
                                                    break

                                except Exception:
                                    pass

                    if(operations and definition):
                        # Define buttons for Slack
                        actions = []

                        for operation in operations:
                            actions.append({
                                    'name': operation['value'],
                                    'text': operation['value'],
                                    'value': _('Explain {0} {1}').format(operation['type'], operation['value'] if operation['type'] == 'operation' else operation['path']),
                                }
                            )

                        attachments = {
                            'text': _('Which operation you want to know more about? Here are top operations:'),
                            'fallback': generic_error_msg,
                            'callback_id': 'object_definition',
                            'actions': actions,
                        }
                        attachments_list = {
                            'text': _('Here is the object definition for *{0}*:\n{1}\n\nI also found these operations linked to it:\n{2}').format(
                                parameters['object'],
                                pprint.pformat(definition),
                                '\n'.join(operation['value'] for operation in operations),
                            ),
                            'attachments': [attachments, ],
                        }
                        data_response = {
                            'slack': attachments_list,
                        }

                        output_data['data'] = data_response

                        # And display text
                        output_data['displayText'] = '\n'.join(operation['value'] for operation in operations)
                    elif(definition):
                        output_data['displayText'] = _('Here is the object definition for *{0}*:\n{1}').format(
                            parameters['object'],
                            pprint.pformat(definition),
                        )
                except KeyError:
                    output_data['displayText'] = not_defined_msg

                except ObjectDoesNotExist:
                    output_data['displayText'] = no_api_msg

            # Operation definitions for specific API
            ########################################
            elif action == 'api.operation':
                try:
                    api = self.get_api(parameters, contexts)
                    parser = self.get_parser(api)
                    try:
                        output_data['displayText'] = _('Here is the operation definition for *{0}*:\n{1}').format(
                            parameters['operation'],
                            pprint.pformat(parser.operation[parameters['operation']]),
                        )
                    except KeyError:
                        output_data['displayText'] = not_defined_msg

                except ObjectDoesNotExist:
                    output_data['displayText'] = no_api_msg

            # Path info for specific API
            ############################
            elif action == 'api.path':
                try:
                    api = self.get_api(parameters, contexts)
                    parser = self.get_parser(api)
                    try:
                        # TODO
                        # This is a dirty dirty fix because due to a bug
                        # in api.ai, the leading / gets stripped
                        # Occasionally check if this is resolved
                        # https://discuss.api.ai/t/slashes-are-removed/5595
                        if parameters['path'] in parser.paths:
                            path = parameters['path']
                        elif '/' + parameters['path'] in parser.paths:
                            path = '/' + parameters['path']
                        elif parser.base_path + '/' + parameters['path'] in parser.paths:
                            path = parser.base_path + '/' + parameters['path']

                        output_data['displayText'] = _('Here is the path definition for *{0}*:\n{1}').format(
                            path,
                            pprint.pformat(parser.paths[path]),
                        )

                        output_data['displayText'] = pprint.pformat(parser.paths[path])

                    except KeyError:
                        output_data['displayText'] = not_defined_msg
                    except Exception:
                        output_data['displayText'] = generic_error_msg

                except ObjectDoesNotExist:
                    output_data['displayText'] = no_api_msg
                except Exception:
                    output_data['displayText'] = generic_error_msg


# TODO
# "securityDefinitions"
   # "securityDefinitions":{
   #    "petstore_auth":{
   #       "type":"oauth2",
   #       "authorizationUrl":"http://petstore.swagger.io/oauth/dialog",
   #       "flow":"implicit",
   #       "scopes":{
   #          "write:pets":"modify pets in your account",
   #          "read:pets":"read your pets"
   #       }
   #    },
   #    "api_key":{
   #       "type":"apiKey",
   #       "name":"api_key",
   #       "in":"header"
   #    }




            # Fallback response
            ###################

            # We have no idea what this intent is...
            else:
                output_data['displayText'] = not_defined_msg

            # For now duplicate the display text and speech
            output_data['speech'] = output_data['displayText']
            serializer = BotResponseSerializer(output_data)
            return Response(serializer.data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
