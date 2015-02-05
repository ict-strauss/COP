"""Swagger output plugin for pyang.
"""

import optparse
import json
import re
import string
from collections import OrderedDict

from pyang import plugin
from pyang import statements


def pyang_plugin_init():
    """ Initialization function called by the plugin loader. """
    plugin.register_plugin(SwaggerPlugin())


class SwaggerPlugin(plugin.PyangPlugin):

    """ Plugin class for swagger file generation."""

    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['swagger'] = self

    def add_opts(self, optparser):
        # A list of command line options supported by the swagger plugin.
        # TODO: which options are really needed?
        optlist = [
            optparse.make_option(
                '--swagger-help',
                dest='swagger_help',
                action='store_true',
                help='Print help on swagger options and exit'),
            optparse.make_option(
                '--swagger-depth',
                type='int',
                dest='swagger_depth',
                default=5,
                help='Number of levels to print'),
            optparse.make_option(
                '--swagger-filename',
                dest='swagger_filename',
                help='Subtree to print'),
            optparse.make_option(
                '--swagger-path',
                dest='swagger_path',
                type='string',
                help='Path to print')]
        optgrp = optparser.add_option_group('Swagger specific options')
        optgrp.add_options(optlist)

    def setup_ctx(self, ctx):
        pass

    def setup_fmt(self, ctx):
        pass

    def emit(self, ctx, modules, fd):
        # TODO: the path variable is currently not used.
        if ctx.opts.swagger_path is not None:
            path = string.split(ctx.opts.swagger_path, '/')
            if path[0] == '':
                path = path[1:]
        else:
            path = None

        emit_swagger_spec(modules, fd, ctx.opts.path)


def print_header(module, fd):
    """ Print the swagger header information."""
    module_name = str(module.arg)
    header = OrderedDict()
    header['swagger'] = '2.0'
    header['info'] = {
        'description': '%s API generated from %s' % (
            module_name, module.pos.ref.rsplit('/', 1)[1]),
        'version': '1.0.0',
        'title': str(module_name + ' API')
    }
    header['host'] = 'localhost:8080'
    # TODO: introduce flexible base path. (CLI options?)
    header['basePath'] = '/restconf/config'
    header['schemes'] = ['http']
    return header


def emit_swagger_spec(modules, fd, path):
    """ Emits the complete swagger specification for the yang file."""
    printed_header = False
    model = OrderedDict()
    definitions = OrderedDict()
    # Go through all modules and extend the model.
    for module in modules:
        if not printed_header:
            model = print_header(module, fd)
            printed_header = True
            path = '/'
        # list() needed for python 3 compatibility
        groupings = list(module.i_groupings.values())
        # Print the swagger definitions of the Yang groupings.
        definitions = gen_model(groupings, definitions)
        # extract children which contain data definition keywords
        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        # generate the APIs for all children
        if len(chs) > 0:
            model['paths'] = OrderedDict()
            gen_apis(chs, path, model['paths'], definitions)
        model['definitions'] = definitions
        fd.write(json.dumps(model, indent=4, separators=(',', ': ')))


def gen_model(children, tree_structure):
    """ Generates the swagger definition tree."""
    referenced = False
    for child in children:
        node = {}
        if hasattr(child, 'substmts'):
            for attribute in child.substmts:
                # process the 'type' attribute:
                # Currently integer, enumeration and string are supported.
                if attribute.keyword == 'type':
                    if attribute.arg[:3] == 'int':
                        node['type'] = 'integer'
                        node['format'] = attribute.arg
                    elif attribute.arg == 'enumeration':
                        node['type'] = 'string'
                        node['enum'] = [e[0]
                                        for e in attribute.i_type_spec.enums]
                    # map all other types to string
                    else:
                        node['type'] = 'string'
                # Process the reference to another model.
                # We differentiate between single and array references.
                elif attribute.keyword == 'uses':
                    ref = to_upper_camelcase(attribute.arg)
                    ref = '#/definitions/' + ref
                    if str(child.keyword) == 'list':
                        node['items'] = {'$ref': ref}
                        node['type'] = 'array'
                    else:
                        node['$ref'] = ref
                        referenced = True
        # When a node contains a referenced model as an attribute the algorithm
        # does not go deeper into the sub-tree of the referenced model.
        if not referenced:
            node = gen_model_node(child, node)
        # Groupings are class names and upper camelcase.
        # All the others are variables and lower camelcase.
        if child.keyword == 'grouping':
            tree_structure[to_upper_camelcase(child.arg)] = node
        else:
            tree_structure[to_lower_camelcase(child.arg)] = node
    # TODO: do we really need this return value? We are working on the
    # reference anyhow.
    return tree_structure


def gen_model_node(node, tree_structure):
    """ Generates the properties sub-tree of the current node."""
    if hasattr(node, 'i_children'):
        properties = {}
        properties = gen_model(node.i_children, properties)
        if properties:
            tree_structure['properties'] = properties
    # TODO: do we need a return value or is the reference enough.
    return tree_structure


def gen_apis(children, path, apis, definitions):
    """ Generates the swagger path tree for the APIs."""
    for child in children:
        gen_api_node(child, path, apis, definitions)
    # TODO: do we need a return value or is the reference enough.
    return apis


# Generates the API of the current node.

def gen_api_node(node, path, apis, definitions):
    """ Generate the API for a node."""
    path += str(node.arg) + '/'
    config = True
    tree = {}
    schema = {}
    for sub in node.substmts:
        # If config is False the API entry is read-only.
        if sub.keyword == 'config':
            # TODO: this is not correct in general because it does not consider
            # inheritance. It should be changed to node.i_config.
            config = sub.arg
        elif sub.keyword == 'key':
            key = sub.arg
        elif sub.keyword == 'uses':
            # Set the reference to a model, previously defined by a grouping.
            schema = {'$ref': '#/definitions/' + to_upper_camelcase(sub.arg)}
    # API entries are only generated from container and list nodes.
    if node.keyword == 'list' or node.keyword == 'container':
        if schema:
            if node.keyword == 'list':
                path += '{' + to_lower_camelcase(key) + '}/'
                apis[str(path)] = print_api(node, config, schema, path)
            elif node.keyword == 'container':
                apis[str(path)] = print_api(node, config, schema, path)
        else:
            # If the container has not a referenced model it is necessary
            # to generate the schema tree based on the node children.

            # In our case we just need to create arrays with references
            # TODO: extend to general case and clean up the branches.
            if node.keyword == 'container':
                for child in node.i_children:
                    if child.keyword == 'list':
                        schema['type'] = 'array'
                    ref_model = [ch for ch in child.substmts
                                 if ch.keyword == 'uses']
                    schema['items'] = {
                        '$ref': '#/definitions/' + to_upper_camelcase(
                            ref_model[0].arg)
                    }
            else:
                # TODO: dead code for our model
                properties = {}
                item = {}
                item = gen_model(node.i_children, tree)
                properties2 = {}
                properties2['properties'] = item
                properties[str(node.arg)] = properties2
                schema['properties'] = properties
            apis[str(path)] = print_api(node, config, schema, path)
    # Generate APIs for children.
    if hasattr(node, 'i_children'):
        gen_apis(node.i_children, path, apis, definitions)


# print the API JSON structure.

def print_api(node, config, ref, path):
    """ Creates the available operations for the node."""
    operations = {}
#     is_list = False
#     if node.keyword == 'list':
#         is_list = True
#     if hasattr(node, 'i_children'):
#         for param in node.i_children:
#             if param.keyword == 'list':
#                 is_list = True
    if config and config != 'false':
        operations['put'] = generate_create(node, ref, path)
        operations['get'] = generate_retrieve(node, ref, path)
        operations['post'] = generate_update(node, ref, path)
        operations['delete'] = generate_delete(node, ref, path)
    else:
        operations['get'] = generate_retrieve(node, ref, path)
    return operations


def get_input_path_parameters(path):
    """"Get the input parameters from the path url."""
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

# CREATE

def generate_create(stmt, schema, path):
    """ Generates the create function definitions."""
    path_params = get_input_path_parameters(path)
    put = {}
    generate_api_header(stmt, put, 'Create')
    # Input parameters
    if path_params:
        put['parameters'] = create_parameter_list(path_params)
    else:
        put['parameters'] = []
    put['parameters'].append(create_body_dict(stmt.arg, schema))
    # Responses
    response = create_responses(stmt.arg)
    put['responses'] = response
    return put


# RETRIEVE

def generate_retrieve(stmt, schema, path):
    """ Generates the retrieve function definitions."""
    path_params = get_input_path_parameters(path)
    get = {}
    generate_api_header(stmt, get, 'Retrieve', stmt.keyword == 'container'
                        and not path_params)
    if path_params:
        # Input parameters
        get['parameters'] = create_parameter_list(path_params)
    # Responses
    response = create_responses(stmt.arg, schema)
    get['responses'] = response
    return get


# UPDATE

def generate_update(stmt, schema, path):
    """ Generates the update function definitions."""
    path_params = get_input_path_parameters(path)
    post = {}
    generate_api_header(stmt, post, 'Update')
    # Input parameters
    post['parameters'] = create_parameter_list(path_params)
    post['parameters'].append(create_body_dict(stmt.arg, schema))
    # Responses
    response = create_responses(stmt.arg)
    post['responses'] = response
    return post


# DELETE

def generate_delete(stmt, ref, path):
    """ Generates the delete function definitions."""
    path_params = get_input_path_parameters(path)
    delete = {}
    generate_api_header(stmt, delete, 'Delete')
    # Input parameters
    if path_params:
        delete['parameters'] = create_parameter_list(path_params)
    # Responses
    response = create_responses(stmt.arg)
    delete['responses'] = response
    return delete


def create_parameter_list(path_params):
    """ Create description from a list of path parameters."""
    param_list = []
    for param in path_params:
        parameter = {}
        parameter['in'] = 'path'
        parameter['name'] = str(param)
        parameter['description'] = 'ID of ' + str(param)[:-3]
        parameter['required'] = True
        parameter['type'] = 'string'
        param_list.append(parameter)
    return param_list


def create_body_dict(name, schema):
    """ Create a body description from the name and the schema."""
    body_dict = {}
    body_dict['in'] = 'body'
    body_dict['name'] = name
    body_dict['schema'] = schema
    body_dict['description'] = 'ID of ' + name
    body_dict['required'] = True
    return body_dict


def create_responses(name, schema=None):
    """ Create generic responses based on the name and an optional schema."""
    response = {
        '200': {'description': 'Successful operation'},
        '400': {'description': 'Invalid ID parameter'},
        '404': {'description': '' + name.capitalize() + ' not found'}
    }
    if schema:
        response['200']['schema'] = schema
    return response


def generate_api_header(stmt, struct, operation, is_collection=False):
    """ Auxiliary function to generate the API-header skeleton.
    The "is_collection" flag is used to decide if an ID is needed.
    """
    struct['summary'] = '%s %s%s' % (
        str(operation), str(stmt.arg),
        ('' if is_collection else ' by ID'))
    struct['description'] = str(operation) + ' operation of resource: ' \
        + str(stmt.arg)
    struct['operationId'] = '%s%s%s' % (str(operation).lower(),
                                        to_upper_camelcase(stmt.arg),
                                        ('' if is_collection else 'ById'))
    struct['produces'] = ['application/json']
    struct['consumes'] = ['application/json']


def to_lower_camelcase(name):
    """ Converts the name string to lower camelcase by using "-" and "_" as
    markers.
    """
    return re.sub(r'(?:\B_|\b\-)([a-zA-Z0-9])', lambda l: l.group(1).upper(),
                  name)


def to_upper_camelcase(name):
    """ Converts the name string to upper camelcase by using "-" and "_" as
    markers.
    """
    return re.sub(r'(?:\B_|\b\-|^)([a-zA-Z0-9])', lambda l: l.group(1).upper(),
                  name)
