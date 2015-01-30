#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Tree output plugin

Idea copied from libsmi.
"""

import optparse
import json
import string
from collections import OrderedDict

from pyang import plugin
from pyang import statements


def pyang_plugin_init():
    plugin.register_plugin(SwaggerPlugin())


class SwaggerPlugin(plugin.PyangPlugin):

    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['swagger'] = self

    def add_opts(self, optparser):
        optlist = [optparse.make_option('--swagger-help',
                   dest='swagger_help', action='store_true',
                   help='Print help on tree symbols and exit'),
                   optparse.make_option('--swagger-depth', type='int',
                   dest='depth', default=5,
                   help='Number of levels to print'),
                   optparse.make_option('--swagger-filename',
                   dest='filename', default='service_call.json',
                   help='Subtree to print'),
                   optparse.make_option('--swagger-path', dest='path',
                   type='string',
                   default='/home/amll/COP/swagger/specs/',
                   help='Subtree to print')]
        g = optparser.add_option_group('Tree output specific options')
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        pass

    def setup_fmt(self, ctx):
        pass

    def emit(self,ctx,modules,fd):

        # TODO: the path provided by pyang is a list and not a string

        if ctx.opts.path is not None:
            path = string.split(ctx.opts.path, '/')
            if path[0] == '':
                path = path[1:]

        # TODO: what is filename used for?

        if ctx.opts.filename is not None:
            filename = ctx.opts.filename
        else:
            path = None
        emit_swagger_spec(modules, fd, ctx.opts.path)


def print_help():
    pass


## Print the swagger header.

def print_header(module, fd):
    module_name = str(module.arg)
    header = OrderedDict()
    header['swagger'] = '2.0'
    header['info'] = {'description': str(module_name
                      + ' API generated from '
                      + module.pos.ref.rsplit('/', 1)[1]),
                      'version': '1.0.0', 'title': str(module_name
                      + ' API')}
    header['host'] = 'localhost:8080'

    # TODO: flexible base path

    header['basePath'] = '/restconf/config'
    header['schemes'] = ['http']
    return header


def emit_swagger_spec(modules, fd, path):
    printed_header = False
    model = OrderedDict()
    definitions = OrderedDict()
    for module in modules:
        if not printed_header:
            model = print_header(module, fd)
            printed_header = True

            # path = '/'+str(module.arg)+':'

            path = '/'

        # It is necessary to modify the names' syntax for swagger code-generation

        if module.i_groupings:
            for group in module.i_groupings:
                module.i_groupings[group].keyword = \
                    safety_syntax_check(group)

        # list() needed for python 3 compatibility

        groupings = list(module.i_groupings.values())

        # Print the swagger definitions from the Yang groupings.

        definitions = gen_model(groupings, definitions)

        # extract children which contain data definition keywords

        chs = filter(lambda ch: ch.keyword \
                     in statements.data_definition_keywords,
                     module.i_children)
        if len(chs) > 0:
            model['paths'] = OrderedDict()
            paths = gen_APIs(chs, path, model['paths'], definitions)

        # model["paths"] = paths

        model['definitions'] = definitions
        fd.write(json.dumps(model, indent=4, separators=(',', ': ')))


# Generates the swagger definitions tree.

def gen_model(chs, tree_structure):
    referenced = False
    for ch in chs:
        node = {}
        if hasattr(ch, 'substmts'):
            for attribute in ch.substmts:

                # process type

                if attribute.keyword == 'type':
                    if attribute.arg[:3] == 'int':
                        node['type'] = 'integer'
                        node['format'] = attribute.arg
                    elif attribute.arg == 'enumeration':
                        node['type'] = 'string'
                        node['enum'] = map(lambda e: e[0],
                                attribute.i_type_spec.enums)
                    else:

                    # map all other types to string

                        node['type'] = 'string'
                elif attribute.keyword == 'uses':
                    ref = safety_syntax_check(attribute.arg)
                    ref = '#/definitions/' + str(ref)
                    if str(ch.keyword) == 'list':
                        node['items'] = {'$ref': ref}
                        node['type'] = 'array'
                    else:
                        node['$ref'] = ref
                        referenced = True

        # When a node contains a referenced model as an attribute
        # the algorithm does not go deeper in the referenced model sub-tree.

        if not referenced:
            node = gen_model_node(ch, node)

        tree_structure[safety_syntax_check(ch.arg)] = node

    return tree_structure


# Generates the properties sub-tree of the current node.

def gen_model_node(ch, tree_structure):
    if hasattr(ch, 'i_children'):
        properties = {}
        properties = gen_model(ch.i_children, properties)
        if properties and not '$ref' in tree_structure:
            tree_structure['properties'] = properties

    return tree_structure


# Generates the swagger path tree.

def gen_APIs(i_children,path,apis,definitions):

    for ch in i_children:
        gen_API_node(ch, path, apis, definitions)

    return apis


# Generates the API of the current node.

def gen_API_node(s,path,apis,definitions):

    path += str(s.arg) + '/'
    config = True
    tree = {}
    schema = {}
    for sub in s.substmts:

        # If config is False the API entry is read-only.

        if sub.keyword == 'config':
            config = sub.arg
        elif sub.keyword == 'key':
            key = sub.arg
        elif sub.keyword == 'uses':

        # Get the reference to a pre-defined model by a grouping.

            ref = safety_syntax_check(sub.arg)
            schema = {'$ref': '#/definitions/' + str(ref)}

    # API entries are only generated from the container and list nodes.

    if s.keyword == 'list' or s.keyword == 'container':
        if schema:
            if s.keyword == 'list':
                path += '{' + str(key) + '}/'
                apis[str(path)] = printAPI(s, config, schema, path)
            elif s.keyword == 'container':
                apis[str(path)] = printAPI(s, config, schema, path)
        else:

        # If the container has not a referenced model it is necessary
        # to generate the schema tree based on the node children.

            # In our case we just need to create arrays with references
            # TODO: extend to general case

            if s.keyword == 'container':
                for child in s.i_children:
                    if child.keyword == 'list':
                        schema['type'] = 'array'
                    test = filter(lambda ch: ch.keyword == 'uses',
                                  child.substmts)
                    schema['items'] = {'$ref': '#/definitions/' \
                            + safety_syntax_check(test[0].arg)}
            else:

            # TODO: dead code for our model

                properties = {}
                item = {}
                item = gen_model(s.i_children, tree)
                properties2 = {}
                properties2['properties'] = item
                properties[str(s.arg)] = properties2
                schema['properties'] = properties
            apis[str(path)] = printAPI(s, config, schema, path)

    if hasattr(s, 'i_children'):
        gen_APIs(s.i_children, path, apis, definitions)


# print the API JSON structure.

def printAPI(ch,config,ref,path):

    operations = {}
    is_list = False
    if ch.keyword == 'list':
        is_list = True
    if hasattr(ch, 'i_children'):
        for param in ch.i_children:
            if param.keyword == 'list':
                is_list = True

    if config != False and config != 'false':

        # print config

        operations['put'] = generateCREATE(ch, is_list, ref, path)
        operations['get'] = generateRETRIEVE(ch, is_list, ref, path)
        operations['post'] = generateUPDATE(ch, is_list, ref, path)
        operations['delete'] = generateDELETE(ch, is_list, ref, path)
    else:
        operations['get'] = generateRETRIEVE(ch, is_list, ref, path)
    return operations


# Get the input paramets in the url

def getInputPathParameters(path):
    path_params = []
    params = path.split('/')
    for param in params:
        if len(param) > 0 and param[0] == '{' and param[len(param) - 1] \
            == '}':
            path_params.append(param[1:-1])
    return path_params


###########################################################
############### Creating CRUD Operations ##################
###########################################################

## CREATE

def generateCREATE(ch,is_list,schema,path):

    path_params = getInputPathParameters(path)
    put = {}
    generateAPIHeader(ch, put, 'Create')

    # # Input parameters

    parameter = {}
    put['parameters'] = []
    if path_params:

        # # Input parameters

        for param in path_params:
            parameter = {}
            parameter['in'] = 'path'
            parameter['name'] = str(param)
            parameter['description'] = 'ID of ' + str(param)[:-3]
            parameter['required'] = True
            parameter['type'] = 'string'
            put['parameters'].append(parameter)
    parameter2 = {}
    parameter2['in'] = 'body'
    parameter2['name'] = str(ch.arg)
    parameter2['schema'] = schema
    parameter2['description'] = 'ID of ' + str(ch.arg)
    parameter2['required'] = True
    put['parameters'].append(parameter2)

    # # Responses

    response = {'200': {'description': 'Successful operation'},
                '400': {'description': 'Invalid ID parameter'},
                '404': {'description': 'Call not found'}}
    put['responses'] = response
    return put


## RETRIEVE

def generateRETRIEVE(ch,is_list,schema,path):

    path_params = getInputPathParameters(path)

    # print path_params

    get = {}
    generateAPIHeader(ch, get, 'Retrieve', ch.keyword == 'container'
                      and not path_params)
    if path_params:
        get['parameters'] = []

        # # Input parameters

        for param in path_params:
            parameter = {}
            parameter['in'] = 'path'
            parameter['name'] = str(param)
            parameter['description'] = 'ID of ' + str(param)[:-3]
            parameter['required'] = True
            parameter['type'] = 'string'
            get['parameters'].append(parameter)

    # # Responses

    response = {'200': {'description': 'Successful operation',
                'schema': schema},
                '400': {'description': 'Invalid ID parameter'},
                '404': {'description': '' + str(ch.arg).capitalize() \
                + ' not found'}}
    get['responses'] = response
    return get


## UPDATE

def generateUPDATE(ch,is_list,schema,path):

    path_params = getInputPathParameters(path)
    post = {}
    generateAPIHeader(ch, post, 'Update')

    # # Input parameters

    post['parameters'] = []

    for param in path_params:
        parameter = {}
        parameter['in'] = 'path'
        parameter['name'] = str(param)
        parameter['description'] = 'ID of ' + str(param)[:-3]
        parameter['required'] = True
        parameter['type'] = 'string'
        post['parameters'].append(parameter)

    parameter2 = {}
    parameter2['in'] = 'body'
    parameter2['name'] = str(ch.arg)
    parameter2['schema'] = schema
    parameter2['description'] = 'ID of ' + str(ch.arg)
    parameter2['required'] = True
    post['parameters'].append(parameter2)

    # # Responses

    response = {'200': {'description': 'Successful operation'},
                '400': {'description': 'Invalid ID parameter'},
                '404': {'description': '' + str(ch.arg).capitalize() \
                + ' not found'}}
    post['responses'] = response
    return post


## DELETE

def generateDELETE(ch,is_list,ref,path):

    path_params = getInputPathParameters(path)
    delete = {}
    generateAPIHeader(ch, delete, 'Delete')

    # # Input parameters

    if path_params:
        parameter = {}
        delete['parameters'] = []
        for param in path_params:
            parameter['in'] = 'path'
            parameter['name'] = str(param)
            parameter['description'] = 'ID of ' + str(param)[:-3]
            parameter['required'] = True
            parameter['type'] = 'string'
            delete['parameters'].append(parameter)

    # # Responses

    response = {'200': {'description': 'Successful operation'},
                '400': {'description': 'Invalid ID parameter'},
                '404': {'description': '' + str(ch.arg).capitalize() \
                + ' not found'}}
    delete['responses'] = response
    return delete


# Aux function to generate the API-header skeleton.

def generateAPIHeader(ch,struct,operation,is_collection=False):

    struct['summary'] = '%s %s%s' % (str(operation),
            str(ch.arg).capitalize(), ('' if is_collection else ' by ID'
            ))
    struct['description'] = str(operation) + ' operation of resource :' \
        + str(ch.arg)
    struct['operationId'] = '%s%s%s' % (str(operation).lower(),
            str(ch.arg).capitalize(), ('' if is_collection else 'byID'))
    struct['produces'] = []
    struct['produces'].append('application/json')
    struct['consumes'] = []
    struct['consumes'].append('application/json')


# Check name for unsupported characters

def safety_syntax_check(name):

    # at the moment just one replacement is needed

    return name.replace('-', '_').capitalize()

