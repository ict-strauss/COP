'''
    List of contributors:
    -Alejandro Aguado (May, 2015), High Performance Networks group, University of Bristol
    [a.aguado@bristol.ac.uk]
    -Arturo Mayoral (May, 2015), Optical Networks & Systems group, Centre Tecnologic de Telecomunicacions de Catalunya (CTTC).
    [arturo.mayoral@cttc.es]


    -Description:
    This code generates a rest api and classes in python (using json description) required for COP.
    Some things are fixed and could change in the future due to changes in json description files.
    Any doubt, bug or suggestion: a.aguado@bristol.ac.uk

'''

import sys
import json
import os
import re
import shutil

sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0])))
from CGConfiguration import CGConfiguration

# jinja code generator
from jinja2 import Environment, PackageLoader
from jinja2_codegen.jinja_classes import *
jinja_env = Environment(loader=PackageLoader('jinja2_codegen', 'templates'), trim_blocks=True, lstrip_blocks=True)

# The regular expression inserted in the url array.
regex_string='(\\w+)'

# Map from JSON types to python types
type_map = {'string' : 'str', 'integer' : 'int'}

def decomposeUrl(string):
    slices=string.split("{")
    varlist=[]
    url=[]
    for sl in slices:
        auxslice=sl.split("}")
        if len(auxslice)!=1:
            varlist.append(auxslice[0])
            url.append(auxslice[1])
        else:
            url.append(auxslice[0])

    defurl=url[0]
    for st in url[1:]:
        defurl+=regex_string+st

    return defurl, varlist


def translateRequest(js):
    ret={}
    res={}
    i=1;
    bp=js['basePath']
    port=int(js['host'].split(":")[-1])
    ret['port']=port
    for path in js['paths'].keys():
        ids={}
        url,variables=decomposeUrl(path)
        msgs=js['paths'][path].keys()
        for method in msgs:
            ids[method]={}
            ids[method]['desc']=js["paths"][path][method]['description']
            ids[method]['resp']=js["paths"][path][method]['responses']
            ids[method]['body']=False
            ids[method]['json']=False
            if 'schemes' in js["paths"][path][method].keys():
                ids[method]['schemes'] = js["paths"][path][method]['schemes']
            if "parameters" in js["paths"][path][method].keys():
                for param in js["paths"][path][method]['parameters']:
                    if "body" in param['in']:
                        ids[method]['body']=True
                        if 'in_params' not in ids[method]:
                            ids[method]['in_params'] = [param['schema']['$ref'].split('/')[-1]]
                        else:
                            ids[method]['in_params'].append(param['schema']['$ref'].split('/')[-1])

            if "application/json" in js["paths"][path][method]['consumes']:
                ids[method]['json']=True
        res["func"+str(i)]={"url":bp+url,"inlineVars":variables, "methods":ids}
        i+=1;
    ret['paths']=res
    return ret


def getType(js):
    if "type" in js.keys():
        if "enum" in js.keys():
            return "enum",[enum for enum in js['enum']],False
        if "integer" in js['type']:
            return js['format'],"none",False
        if "string" in js['type']:
            return "string","none",False
        if "boolean" in js['type']:
            return "boolean","none",False
        if "array" in js['type']:
            if "type" in js['items'].keys():
                return "array", js['items']['type'],False
            elif "$ref" in js['items'].keys():
                return "array",js['items']['$ref'].split("/")[-1],True
            else:
                return "none","none", False
        if "object" in js['type']:
            if "type" in js['additionalProperties'].keys():
                return "object", js['additionalProperties']['type'],False
            elif "$ref" in js['additionalProperties'].keys():
                return "object",js['additionalProperties']['$ref'].split("/")[-1],True
            else:
                return "none","none", False
        else:
            return "none","none", False
    elif "$ref" in js.keys():
        return "import",js['$ref'].split("/")[-1],True
    else:
        return "none","none", False


def translateClasses(js):
    res=[]
    for klass in js['definitions'].keys():
        imports=[]
        cl={}
        atts=[]
        cl['class']=klass
        if 'discriminator' in js['definitions'][klass]:
            cl["discriminator"] = js['definitions'][klass]['discriminator']
        # Special case where the model extending a father class
        if 'allOf' in js['definitions'][klass]:
            for item in js['definitions'][klass]['allOf']:
                if "$ref" in item:
                    cl['extend_class'] = item['$ref'].split("/")[-1]
                elif "properties" in item:
                    for att in item['properties'].keys():
                        taip,other,imp=getType(item['properties'][att])
                        atts.append({"att":att,"type":taip,"other":other})
                        if imp:
                            if other not in imports:
                                imports.append(other)
        else:
            for att in js['definitions'][klass]['properties'].keys():
                taip,other,imp=getType(js['definitions'][klass]['properties'][att])
                atts.append({"att":att,"type":taip,"other":other})
                if imp:
                    if other not in imports:
                        imports.append(other)
        cl["atts"]=atts
        cl["imports"]=imports
        res.append(cl)
    return res


def tab(n):
    return "    "*n


def handleResponse(ident, description, schema=None):
    if "200" in ident:
        if schema!=None:
            return 'raise Successful("'+description+'",json.dumps(js))'
        else:
            return 'raise Successful("'+description+'",json.dumps(js))'
    elif "404" in ident:
        return 'raise NotFoundError("'+description+'")'
    elif "400" in ident:
        return 'raise BadRequestError("'+description+'")'
    else:
        return 'print "There is something wrong with responses"'

def getNotificationAPIs(data):
    notification_urls = []
    for element in data['paths']:
        methods = data['paths'][element]['methods']
        for method in methods:
            if 'schemes' in methods[method].keys():
                if 'ws' in methods[method]['schemes']:
                    notification_urls.append(data['paths'][element])
    return notification_urls


## This function generates a HTTP Server which will serve as a unique access point to our COP server implementation.
def generateServerStub(restname, data, services, path):
    import_list = []
    urls_list = []
    for serv in services:
        import_list.append(ImportObject('',serv.replace("-","_")))
        urls_list.append(serv.replace("-","_") + '.urls')

    # use jinja
    template = jinja_env.get_template('server.py')
    rendered_string = template.render(import_list=import_list, urls_list=urls_list,
                                      port=data['port'])

    # write server file
    out = open(path+restname+".py","w+")
    out.write(rendered_string)
    out.close()


def generateNotificationServer(name, data, notfy_urls, path):
    class_list=[]
    dictio = {}
    base_url = ''
    for element in notfy_urls:
        base_url = '/'.join(element['url'].split('/')[:-2])
        url = to_upper_camelcase(element['url'].split('/')[-2])+"Service"
        lower_url = "/"+to_lower_camelcase(element['url'].split('/')[-2])+"Service"
        dictio[str(base_url)+str(lower_url)] = str(url)
        class_list.append(url)

    servicemap = []
    for element in dictio:
        servicemap.append("\'"+str(element)+"\' : "+str(dictio[element]))

    # use jinja
    template = jinja_env.get_template('notification_server.py')
    rendered_string = template.render(servicemap=servicemap, class_list=class_list)

    # write notifiction server file
    out = open(path+name+".py","w+")
    out.write(rendered_string)
    out.close()


def generateRESTapi(data, name, imp, restname, params, services, path, notfy_urls):
    #if not os.path.isfile("server.py"):
    generateServerStub("server", data, services, path)
    if notfy_urls:
        generateNotificationServer("notification_factory", data, notfy_urls, path)

    info=data['paths']
    name_classes = {}
    params_callback = {}

    url_object_list = []
    
    for func in info.keys():
        # Here we generate the name of the class and its related callback to the backend program based on the API syntax of each function.
        list_element_url = info[func]['url'].split('/')
        indexes=[i for i,element in enumerate(list_element_url[3:-1]) if element == regex_string]
        name_classes[func] = "".join([info[func]["inlineVars"][indexes.index(i)].title() if element == regex_string else element.title() for i,element in enumerate(list_element_url[3:-1])])
        params_callback[func] = ",".join([info[func]["inlineVars"][indexes.index(i)] for i,element in enumerate(list_element_url[3:-1]) if element == regex_string])
        url = info[func]['url']
        callback = restname + "." + name_classes[func]
        url_object_list.append(UrlObject(url, callback))

    # imports of functions
    functions_import_list = []
    for func in info.keys():
        file = "funcs_" + restname + "." + name_classes[func][0].lower() + name_classes[func][1:] + "Impl"
        name = name_classes[func] + "Impl"
        functions_import_list.append(ImportObject(file, name))
    
    # imports of objects
    objects_import_list = []
    for im in imp:
        file = "objects_" + restname + "." + im[0].lower() + im[1:]
        name = im
        objects_import_list.append(ImportObject(file, name))

    ret={}
    callback_list = []
    for func in info.keys():
        # Create funcs with inlineVars
        ret[func+"Handle"]=[]
        method_list = []
        arguments = ['self'] + info[func]["inlineVars"]
        for method in info[func]['methods'].keys():
            ret[func+"Handle"].append(method)
            name = method
            printstr = info[func]['methods'][method]['desc']
            new_object = None
            impl_arguments = None
            json_parser = None
            response = None
            if info[func]['methods'][method]['body']:
                web_data_body = True
                if info[func]['methods'][method]['json']:
                    json_parser = True
                    new_object = info[func]['methods'][method]['in_params'][0]
                    if len(params_callback[func]) > 0:
                        response = True
                        impl_arguments = params_callback[func]
                    else:
                        response = False
                else:
                    json_parser = False
            else:
                web_data_body = False
                impl_arguments = params_callback[func]
            response_list = []
            for resp in info[func]['methods'][method]["resp"].keys():
                if "schema" in info[func]['methods'][method]["resp"][resp].keys():
                    handleResp = handleResponse(resp, info[func]['methods'][method]["resp"][resp]['description'], info[func]['methods'][method]["resp"][resp]["schema"])
                    jotason = True
                else:
                    handleResp = handleResponse(resp, info[func]['methods'][method]["resp"][resp]['description'])
                    jotason = False
                response_list.append(ResponseObject(jotason, handleResp))
            method_list.append(CallbackMethodObject(name, printstr, web_data_body,
                                                    json_parser, new_object, response, impl_arguments,
                                                    response_list))
        url = info[func]['url']
        name = name_classes[func]
        callback_list.append(CallbackObject(name, url, method_list, arguments))

    if params.isAuth:
        auth=True
        users=json.dumps(params.users)
    else:
        auth=False
        users=None
    if params.isCORS:
        cors = True
        url = params.url
    else:
        cors = False
        url = None

    # use jinja
    template = jinja_env.get_template('api.py')
    rendered_string = template.render(auth=auth,
                                      users=users,
                                      cors=cors,
                                      url=url,
                                      web_data_body=web_data_body,
                                      functions_import_list=functions_import_list,
                                      objects_import_list=objects_import_list,
                                      url_object_list=url_object_list,
                                      callback_list=callback_list,
                                      )

    # write API file
    out=open(path + restname+".py","w+")
    out.write(rendered_string)
    out.close()
    return ret

def translate_type_json2python(typename):
    if typename in type_map:
        return type_map[typename]
    else:
        return typename

def generateAttributeValue(att): #Initialization of different attributes
    if "string" in att['type']:
        return '""'
    elif "int" in att['type']:
        return '0'
    elif "boolean" in att['type']:
        return 'False'
    elif "array" in att['type']:
        return "ArrayType(" + translate_type_json2python(att['other']) + ")"
    elif "object" in att['type']:
        return "{} #dict of " + att['other']
    elif "import" in att['type']:
        return att['other']+"() #import"
    elif "enum" in att['type']:
        return att['att'].capitalize() + '(1)'
    else:
        return text+"None #FIXME: This parameter is not well defined"


def generateClasses(data, restname, path):
    # Create folder objects_
    if not os.path.exists(path+"objects_"+restname+"/"):
        os.makedirs(path+"objects_"+restname+"/")

    # Create __init__.py file
    out=open(path+"objects_"+restname+"/__init__.py","w+")
    out.write(" ")
    out.close()

    # Create class.py files
    for klass in data:
        name=klass['class']

        import_list = []
        attribute_list = []
        enum_list = []

        imports = klass['imports']
        if 'extend_class' in klass:
            klass['imports'].append(klass['extend_class'])
        else:
            for klass2 in data:
                if 'extend_class' in klass2 and klass2['extend_class'] in klass['imports']:
                    imports.append(klass2['class'])

        # imports
        for imp in imports:
            imp_file = imp[0].lower()+imp[1:]
            import_list.append(ImportObject(imp_file, imp))

        import_list.append(ImportObject('objects_common.jsonObject', 'JsonObject'))
        import_list.append(ImportObject('objects_common.arrayType', 'ArrayType'))
        import_list.append(ImportObject('objects_common.enumType', 'EnumType'))

        # determine superclass
        if 'extend_class' in klass:
            superclass_name = klass['extend_class']
        else:
            superclass_name = 'JsonObject'

        # attributes
        for att in klass['atts']:
            attribute_list.append(AttributeObject(att['att'], generateAttributeValue(att)))

        # enums
        for att in klass['atts']:
            if "enum" in att['type']:
                enum_values = [ '\'' + x + '\'' for x in att['other'] ]
                enum_list.append(EnumObject(att['att'].capitalize(), enum_values))

        # use jinja
        template = jinja_env.get_template('object.py')
        rendered_string = template.render(import_list=import_list,
                                          attribute_list=attribute_list,
                                          enum_list=enum_list,
                                          class_name=name,
                                          superclass_name=superclass_name)

        #write class file
        out=open(path+"objects_"+restname+"/"+name[0].lower()+name[1:]+".py","w+")
        out.write(rendered_string)
        out.close()


def generateCallableClasses(funcs, data, imp, restname, path):
    # create folder funcs_
    if not os.path.exists(path+"funcs_"+restname+"/"):
        os.makedirs(path+"funcs_"+restname+"/")
        out=open(path+"funcs_"+restname+"/__init__.py","w+")
        out.write(" ")
        out.close()

    info=data['paths']
    name_classes = {}
    params_callback = {}

    for func in info.keys():
        # Here we generate the name of the class_name and its related callback_name to the backend program based on the API syntax of each function.
        list_element_url = info[func]['url'].split('/')
        indexes=[i for i,element in enumerate(list_element_url[3:-1]) if element == regex_string]
        name_classes[func] = "".join([info[func]["inlineVars"][indexes.index(i)].title() if element == regex_string else element.title() for i,element in enumerate(list_element_url[3:-1])])
        params_callback[func]= [info[func]["inlineVars"][indexes.index(i)] for i,element in enumerate(list_element_url[3:-1]) if element == regex_string]

        class_name = name_classes[func]
        method_list = []
        for method in info[func]['methods'].keys():
            if len (params_callback[func]) > 0:
                ## Input body parameters are included into the class headers if so.
                if (method in ['put','post']) and ('in_params' in info[func]['methods'][method]):
                    in_params = [element.lower() for element in info[func]['methods'][method]['in_params']]
                    arguments = params_callback[func] + in_params
                else:
                    arguments = params_callback[func]
            else:
                if (method in ['put','post']) and ('in_params' in info[func]['methods'][method]):
                    arguments = [element.lower() for element in info[func]['methods'][method]['in_params']]
                else:
                    arguments = []
            if 'in_params' in info[func]['methods'][method]:
                printstr = info[func]['methods'][method]['in_params'][0].lower()
            else:
                printstr = ''
            method_list.append(MethodObject(method, arguments, printstr))

        # use jinja
        template = jinja_env.get_template('callable.py')
        rendered_string = template.render(class_name=class_name,
                                          method_list=method_list)

        # write callable file
        out=open(path+"funcs_"+restname+"/"+name_classes[func][0].lower()+name_classes[func][1:]+"Impl.py","w+")
        out.write(rendered_string)
        out.close()


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


if len(sys.argv)==1:
    print "Filename argument required"
else:
    filename=sys.argv[1]
    if len(sys.argv)>2:
        path=sys.argv[2]
    else:
        path = ""
    params = CGConfiguration(os.path.abspath(os.path.dirname(sys.argv[0]))+"/CGConfiguration.xml")
    if  len(path)>0 and path[-1]!="/":
        path+="/"

    f=open(filename, 'rb')
    service=filename.split("/")[-1].split(".")[0]
    name=service+".py"
    restname=service.replace("-","_")

    stri=f.read()
    js=json.loads(stri)
    #Translate json into a more manageable structure
    jsret=translateClasses(js)
    #print json.dumps(jsret)
    #generating classes first
    print "Generating Rest Server and Classes for "+name
    print "classes could be found in '"+path+"objects_"+restname+"/' folder"
    generateClasses(jsret,restname, path)
    imp=[]
    services=[]
    if not os.path.exists(path+".cop/"):
        os.makedirs(path+".cop/")
    if os.path.isfile(path+".cop/services.json"):
        servicefile=open(path+".cop/services.json", 'rb')
        services=json.loads(servicefile.read())
        servicefile.close()

    #copy common objects
    srcdir = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'objects_common')
    dstdir = os.path.join(path, 'objects_common')
    shutil.copytree(srcdir, dstdir)

    #create imports for the main class (in case the user needs to use them)
    for klass in jsret:
        imp.append(klass['class'])
    #generate (is any) the RESTful Server
    if "paths" in js.keys():
        if service not in services:
            services.append(service)
        jsret2=translateRequest(js)
        notfy_urls = getNotificationAPIs(jsret2)
        ret=generateRESTapi(jsret2,name,imp, restname,params, services, path, notfy_urls)
        generateCallableClasses(ret,jsret2, imp, restname, path)
    servicefile=open(path+".cop/services.json", 'w+')
    servicefile.write(json.dumps(services))
    servicefile.close()
    print "Finished"

