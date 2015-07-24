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
from jinja2_codegen.jinja_classes import ImportObject, AttributeObject, EnumObject, MethodObject
jinja_env = Environment(loader=PackageLoader('jinja2_codegen', 'templates'))

# The regular expression inserted in the url array.
regex_string='(\\w+)'

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


def generateParameters(inlineVars):
    ret="(self,"
    for variable in inlineVars:
        ret+=variable+","
    return ret[:-1]+"):"

def handleResponse(ident,description,schema=None):
    #ret=""
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


## This function generates a HTTP Server which will serve as a unique access point to our COP server implementation.
def generateServerStub(restname, data, services, path):

    import_list = []
    urls_list = []
    for serv in services:
        import_list.append(ImportObject('',serv.replace("-","_")))
        urls_list.append(serv.replace("-","_"))

    # use jinja
    template = jinja_env.get_template('server.py')
    rendered_string = template.render(import_list=import_list, urls_list=urls_list,
                                      port=data['port'])

    # write server file
    out = open(path+restname+".py","w+")
    out.write(rendered_string)
    out.close()


def generateRESTapi(data, name, imp, restname, params, services, path):
    #if not os.path.isfile("server.py"):
    generateServerStub("server", data, services, path)

    index=0
    line="\n"
    out=open(path + restname+".py","w+")

    urls="( "
    info=data['paths']

    name_classes = {}
    params_callback = {}
    for func in info.keys():
        # Here we generate the name of the class and its related callback to the backend program based on the API syntax of each function.
        list_element_url = info[func]['url'].split('/')
        indexes=[i for i,element in enumerate(list_element_url[3:-1]) if element == regex_string]
        name_classes[func] = "".join([info[func]["inlineVars"][indexes.index(i)].title() if element == regex_string else element.title() for i,element in enumerate(list_element_url[3:-1])])
        params_callback[func] = ",".join([info[func]["inlineVars"][indexes.index(i)] for i,element in enumerate(list_element_url[3:-1]) if element == regex_string])

        urls+="\""+info[func]['url']+"\" , \""+restname+"."+name_classes[func]+"\" , \n\t"

    #imports
    out.write("import web\nimport json"+line)
    if params.isAuth:
        out.write("import base64\nimport re"+line)
    out.write(line+"# BACKEND FUNCTIONS"+line)
    for func in info.keys():
        out.write("from funcs_"+restname+"."+name_classes[func][0].lower()+name_classes[func][1:]+"Impl import "+name_classes[func]+"Impl"+line)

    out.write(line+"# CALLABLE OBJECTS"+line)
    for im in imp:
        out.write("from objects_"+restname+"."+im[0].lower()+im[1:]+" import "+im+line)

    out.write(line)
    urls=urls[:-2]+")"

    #urls and app initialization
    out.write("urls = "+urls+line+line)
    if (params.isAuth):
        out.write("users = "+json.dumps(params.users)+line+line)
    #error functions
    out.write("class NotFoundError(web.HTTPError):\n"+tab(1)+"def __init__(self,message):\n"+tab(2)+"status = '404 '+message\n"+tab(2)+"headers = {'Content-Type': 'text/html'}\n"+tab(2)+"data = '<h1>'+message+'</h1>'\n"+tab(2)+"web.HTTPError.__init__(self, status, headers, data)"+line+line)
    out.write("class BadRequestError(web.HTTPError):\n"+tab(1)+"def __init__(self,message):\n"+tab(2)+"status = '400 '+message\n"+tab(2)+"headers = {'Content-Type': 'text/html'}\n"+tab(2)+"data = '<h1>'+message+'</h1>'\n"+tab(2)+"web.HTTPError.__init__(self, status, headers, data)"+line+line)
    out.write("class Successful(web.HTTPError):\n"+tab(1)+"def __init__(self,message,info=''):\n"+tab(2)+"status = '200 '+message\n"+tab(2)+"headers = {'Content-Type': 'application/json'}\n"+tab(2)+"data = info\n"+tab(2)+"web.HTTPError.__init__(self, status, headers, data)"+line+line)
    ret={}
    if (params.isAuth):
        out.write("class basicauth:"+line+line)
        index+=1
        out.write(tab(index)+"@classmethod"+line)
        out.write(tab(index)+"def check(self,auth):"+line)
        index+=1
        out.write(tab(index)+"if auth is not None:"+line)
        index+=1
        out.write(tab(index)+'auth2 = re.sub("^Basic ","", auth)'+line)
        out.write(tab(index)+"user,pswd = base64.decodestring(auth2).split(':')"+line)
        out.write(tab(index)+"if user in users.keys() and pswd == users[user]:"+line)
        index+=1
        out.write(tab(index)+"return True"+line)
        index-=1
        out.write(tab(index)+"else:"+line)
        index+=1
        out.write(tab(index)+"return False"+line)
        index-=2
        out.write(tab(index)+"else:"+line)
        index+=1
        out.write(tab(index)+"return False"+line+line)
        index-=3
    for func in info.keys():
        # Create class
        out.write("#"+info[func]['url']+line)
        out.write("class "+name_classes[func]+":"+line+line)
        # Create funcs with inlineVars
        ret[func+"Handle"]=[]
        for method in info[func]['methods'].keys():
            index+=1
            out.write(tab(index)+"def "+method.upper()+generateParameters(info[func]["inlineVars"])+line)
            index+=1
            ret[func+"Handle"].append(method)
            if params.isAuth:
                out.write(tab(index)+'if not basicauth.check(web.ctx.env.get("HTTP_AUTHORIZATION")):'+line)
                index+=1
                out.write(tab(index)+"web.header('WWW-Authenticate','Basic realm=")
                out.write('"Auth example"')
                out.write("')"+line)
                out.write(tab(index)+"web.ctx.status = '401 Unauthorized'"+line)
                out.write(tab(index)+"return 'Unauthorized'"+line)
                index-=1
            out.write(tab(index)+"print \""+info[func]['methods'][method]['desc']+"\""+line)
            if params.isCORS:
                out.write(tab(index)+"web.header('Access-Control-Allow-Origin','"+params.url+"')"+line)

            if info[func]['methods'][method]['body']:
                out.write(tab(index)+"data=web.data() #data in body"+line)
                if info[func]['methods'][method]['json']:
                    out.write(tab(index)+"input_json=json.loads(data) #json parser."+line)
                    out.write(tab(index)+"input="+info[func]['methods'][method]['in_params'][0]+"(input_json) #It creates an object instance from the json_input data."+line)

                    if len(params_callback[func])>0:
                        out.write(tab(index)+"response = "+name_classes[func]+"Impl."+method+"("+params_callback[func]+", input)"+line)
                    else:
                        out.write(tab(index)+"response = "+name_classes[func]+"Impl."+method+"(input)"+line)
            else:
                out.write(tab(index)+"response = "+name_classes[func]+"Impl."+method+"("+params_callback[func]+")"+line)

            for resp in info[func]['methods'][method]["resp"].keys():
                jotason=False
                if "schema" in info[func]['methods'][method]["resp"][resp].keys():
                    handleResp=handleResponse(resp, info[func]['methods'][method]["resp"][resp]['description'],info[func]['methods'][method]["resp"][resp]["schema"])
                    jotason=True
                else:
                    handleResp=handleResponse(resp, info[func]['methods'][method]["resp"][resp]['description'])
                if jotason:
                    out.write(tab(index)+"#js={} #Uncomment to create json response"+line)
                out.write(tab(index)+"#"+handleResp+" #Uncomment to handle responses"+line)
            out.write(tab(index)+"raise Successful('Successful operation','{\"description\":\""+info[func]['methods'][method]['desc']+"\"}')"+line)
            index-=1
            out.write(line)
            index-=1
        if params.isCORS:
            index+=1
            out.write(tab(index)+"def OPTIONS"+generateParameters(info[func]["inlineVars"])+line)
            index+=1
            out.write(tab(index)+"web.header('Access-Control-Allow-Origin','"+params.url+"')"+line)
            out.write(tab(index)+"web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')"+line)
            text="raise Successful('Successful operation','{"
            text+='"description":"Options called CORS"}'
            text+="')"
            out.write(tab(index)+text+line+line)
            index-=1
            index-=1

    out.close()
    return ret

def generateAttributeValue(att): #Initialization of different attributes
    if "string" in att['type']:
        return '""'
    elif "int" in att['type']:
        return '0'
    elif "boolean" in att['type']:
        return 'False'
    elif "array" in att['type']:
        return "ArrayType(" + att['other'] + ")"
    elif "object" in att['type']:
        return "{} #dict of " + att['other']
    elif "import" in att['type']:
        return att['other']+"() #import"
    elif "enum" in att['type']:
        return '0'
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

        # imports
        for imp in klass['imports']:
            imp_file = imp[0].lower()+imp[1:]
            import_list.append(ImportObject(imp_file, imp))
        import_list.append(ImportObject('objects_common.jsonObject', 'JsonObject'))
        import_list.append(ImportObject('objects_common.arrayType', 'ArrayType'))

        # attributes
        for att in klass['atts']:
            attribute_list.append(AttributeObject(att['att'], generateAttributeValue(att)))

        # enums
        for att in klass['atts']:
            if "enum" in att['type']:
                enum_list.append(EnumObject(att['att'].capitalize(), att['other']))

        # use jinja
        template = jinja_env.get_template('object.py')
        rendered_string = template.render(import_list=import_list,
                                          attribute_list=attribute_list,
                                          enum_list=enum_list,
                                          class_name=name,
                                          superclass_name='JsonObject')

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

    template = jinja_env.get_template('callable.py')

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
        rendered_string = template.render(class_name=class_name,
                                          method_list=method_list)

        # write callable file
        out=open(path+"funcs_"+restname+"/"+name_classes[func][0].lower()+name_classes[func][1:]+"Impl.py","w+")
        out.write(rendered_string)
        out.close()


def is_inheritted_class(data, att):
    for child_klass in data:
        if child_klass['class'] == att['other']:
            if 'discriminator' in child_klass.keys():
                return True
    return False

def get_child_classes(data, att):
    child_classes = []
    for child_klass in data:
        if child_klass['class'] == att['other']:
            discriminator = child_klass['discriminator']
            for att2 in child_klass['atts']:
                if att2['att'] == discriminator:
                    _type = att2['type']
                    print _type
        if 'extend_class' in child_klass.keys():
            if child_klass['extend_class'] == att['other']:
                child_classes.append(child_klass['class'])

    return {'discriminator':discriminator, 'child_classes':child_classes, 'type':_type}


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
        ret=generateRESTapi(jsret2,name,imp, restname,params, services, path)
        generateCallableClasses(ret,jsret2, imp, restname, path)
    servicefile=open(path+".cop/services.json", 'w+')
    servicefile.write(json.dumps(services))
    servicefile.close()
    print "Finished"

