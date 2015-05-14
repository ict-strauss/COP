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

def decomposeUrl(str):
    slices=str.split("{")
    varlist=[]
    url=[]
    for slice in slices:
        auxslice=slice.split("}")
        if len(auxslice)!=1:
            varlist.append(auxslice[0])
            url.append(auxslice[1])
        else:
            url.append(auxslice[0])

    defurl=""
    for st in url:
        defurl+=st+"(.*)"

    return defurl[:-4],varlist

def translateRequest(js):
    ret={}
    res={}
    i=1;
    bp=js['basePath']
    port=int(js['host'].split(":")[-1])
    ret['port']=port
    for path in js['paths'].keys():
        ids={}
        url,vars=decomposeUrl(path)
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
            if "application/json" in js["paths"][path][method]['consumes']:
                ids[method]['json']=True
        res["func"+str(i)]={"url":bp+url,"inlineVars":vars, "methods":ids}
        i+=1;
    ret['paths']=res
    return ret

def getType(js):
    if "type" in js.keys():
        if "integer" in js['type']:
            return js['format'],"none",False
        if "string" in js['type']:
            return "string","none",False
        if "array" in js['type']:
            if "type" in js['items'].keys():
                return "array", js['items']['type'],False
            elif "$ref" in js['items'].keys():
                return "array",js['items']['$ref'].split("/")[-1],True
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
    for var in inlineVars:
        ret+=var+","
    return ret[:-1]+"):"

def handleResponse(id,description,schema=None):
    ret=""
    if "200" in id:
        if schema!=None:
            return 'raise Successful("'+description+'",json.dumps(js))'
        else:
            return 'raise Successful("'+description+'",json.dumps(js))'
    elif "404" in id:
        return 'raise NotFoundError("'+description+'")'
    elif "400" in id:
        return 'raise BadRequestError("'+description+'")'
    else:
        return 'print "There is something wrong with responses"'


def generateRESTapi(data,name,imp, restname):
	index=0
	line="\n"
	out=open(name,"w+")

	urls="( "
	info=data['paths']
	name_classes = {}
	params_callback = {}
	for func in info.keys():
		# Here we generate the name of the class and its related callback to the backend program based on the API syntax of each function.
		list_element_url = info[func]['url'].split('/')
		indexes=[i for i,element in enumerate(list_element_url[3:-1]) if element == '(.*)']
		name_classes[func] = "".join([info[func]["inlineVars"][indexes.index(i)].title() if element == '(.*)' else element.title() for i,element in enumerate(list_element_url[3:-1])])
		params_callback[func] = "("+",".join([info[func]["inlineVars"][indexes.index(i)] for i,element in enumerate(list_element_url[3:-1]) if element == '(.*)'])+")"

		urls+="\""+info[func]['url']+"\" , \""+name_classes[func]+"\" , \n\t"

	#imports
	out.write("import web\nimport json"+line)
	out.write(line+"# BACKEND FUNCTIONS"+line)
	for func in info.keys():
		out.write("from funcs_"+restname+"."+name_classes[func][0].lower()+name_classes[func][1:]+"Impl import "+name_classes[func]+"Impl"+line)

	out.write(line+"# CALLABLE OBJECTS"+line)
	for im in imp:
		out.write("from objects_"+restname+"."+im.lower()+" import "+im+line)

	out.write(line)
	out.write("class MyApplication(web.application):\n"+tab(1)+"def run(self, port=8080, *middleware):\n"+tab(2)+"func = self.wsgifunc(*middleware)\n"+tab(2)+"return web.httpserver.runsimple(func, ('0.0.0.0', port))"+line+line)
	urls=urls[:-2]+")"

	#urls and app initialization
	out.write("urls = "+urls+line)
	out.write("app = MyApplication(urls, globals())"+line+line)
	#error functions
	out.write("class NotFoundError(web.HTTPError):\n"+tab(1)+"def __init__(self,message):\n"+tab(2)+"status = '404 '+message\n"+tab(2)+"headers = {'Content-Type': 'text/html'}\n"+tab(2)+"data = '<h1>'+message+'</h1>'\n"+tab(2)+"web.HTTPError.__init__(self, status, headers, data)"+line+line)
	out.write("class BadRequestError(web.HTTPError):\n"+tab(1)+"def __init__(self,message):\n"+tab(2)+"status = '400 '+message\n"+tab(2)+"headers = {'Content-Type': 'text/html'}\n"+tab(2)+"data = '<h1>'+message+'</h1>'\n"+tab(2)+"web.HTTPError.__init__(self, status, headers, data)"+line+line)
	out.write("class Successful(web.HTTPError):\n"+tab(1)+"def __init__(self,message,info=''):\n"+tab(2)+"status = '200 '+message\n"+tab(2)+"headers = {'Content-Type': 'application/json'}\n"+tab(2)+"data = info\n"+tab(2)+"web.HTTPError.__init__(self, status, headers, data)"+line+line)
	ret={}
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
			out.write(tab(index)+"print \""+info[func]['methods'][method]['desc']+"\""+line)
			if (info[func]['methods'][method]['body']):
				out.write(tab(index)+"data=web.data() #data in body"+line)
				if (info[func]['methods'][method]['json']):
					out.write(tab(index)+"input=json.loads(data) #json data as input"+line)
			out.write(tab(index)+"#from funcs_"+restname+"."+func+"Handle import "+func+"Handle"+line)
			out.write(tab(index)+"response = "+name_classes[func]+"Impl."+method+params_callback[func]+" #You should uncomment and create this class to handle this request"+line)

			#FIXME LEGACY CALLBACK : out.write(tab(index)+"#response = "+func+"Handle()."+method+"() #You should uncomment and create this class to handle this request"+line) #The names of the classes could change. See how to fix them
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

	out.write("if __name__ == \"__main__\":"+line)
	index+=1
	out.write(tab(index)+"app.run("+str(data['port'])+")"+line)
	index-=1
	out.close()
	return ret

def generateAttribute(att): #Initialization of different attributes
    text="self."+att['att']+"="
    if "string" in att['type']:
        return text+'""'
    elif "int" in att['type']:
        return text+'0'
    elif "array" in att['type']:
        return text+"[] #array of "+att['other']
    elif "import" in att['type']:
        return text+att['other']+"() #import"
    else:
        return text+"None #FIXME: This parameter is not well defined"

def generateClasses(data, restname):
	line="\n"
	if not os.path.exists("objects_"+restname+"/"):
		os.makedirs("objects_"+restname+"/")
	out=open("objects_"+restname+"/__init__.py","w+")
	out.write(" "+line)
	out.close()
	for klass in data:
		index=0
		name=klass['class']
		imports=klass['imports']
		atts=klass['atts']
		out=open("objects_"+restname+"/"+name.lower()+".py","w+")
		#Necessary imports
		for imp in imports:
			out.write("from "+imp.lower()+" import "+imp+line)
		out.write(line)
		#Main class
		out.write("class "+name+":"+line+line)
		index+=1
		#Init function
		out.write(tab(index)+"def __init__(self):"+line)
		index+=1
		for att in klass['atts']:
			out.write(tab(index)+generateAttribute(att)+line)
		out.write(line)
		index-=1
		#optional functions -->toJson
		out.write(tab(index)+"def json_serializer(self):"+line)
		index+=1
		out.write(tab(index)+"ret={}"+line)
		for att in klass['atts']:
			if ("array" in att['type']) and (att['other'] in imports):
				out.write(tab(index)+"ret['"+att['att']+"']=[]"+line)
				out.write(tab(index)+"for a in self."+att['att']+":"+line)
				index+=1
				out.write(tab(index)+"ret['"+att['att']+"'].append(a.json_serializer())"+line)
				index-=1
			elif "import" in att['type']:
				out.write(tab(index)+"ret['"+att['att']+"']=self."+att['att']+".json_serializer()"+line)
			else:
				out.write(tab(index)+"ret['"+att['att']+"']=self."+att['att']+line)
		out.write(tab(index)+"return ret"+line)
		index-=1
		#optional function --> __str__
		out.write(line+tab(index)+"def __str__(self):")
		index+=1
		out.write(line+tab(index)+"return str(self.json_serializer())"+line)
		index-=1
		#optional function --> load_json
		out.write(line+tab(index)+"def load_json(self, json_string):"+line)
		index+=1
		out.write(tab(index)+"for key in ("+line)
		index+=1
		for i,att in enumerate(klass['atts']):
			out.write(tab(index)+"'"+att['att']+"'")
			if i != len(klass['atts'])-1:
				out.write(","+line)
		out.write(line+tab(index)+"):"+line)
		out.write(tab(index)+"if key in json_string:"+line)
		index+=1
		first = 0
		for att in klass['atts']:
			if "import" in att['type']:
				if first == 0:
					first = 1
					out.write(tab(index)+'if key == "'+att['att']+'":'+line)
				else:
					out.write(tab(index)+'elif key == "'+att['att']+'":'+line)
				index+=1
				out.write(tab(index)+'self.'+att['att']+' = '+att['other']+'(json_string=json_string[key])'+line)
				index+=-1
		if first !=0:
			out.write(tab(index)+'else:'+line)
			index+=1
		out.write(tab(index)+'setattr(self, key, json_string[key])'+line)

		out.close()

def generateCallableClasses(funcs, data, restname):
	line="\n"
	if not os.path.exists("funcs_"+restname+"/"):
		os.makedirs("funcs_"+restname+"/")
		out=open("funcs_"+restname+"/__init__.py","w+")
		out.write(line)
		out.close()
	index=0
	info=data['paths']
	name_classes = {}
	params_callback = {}
	for func in info.keys():
		# Here we generate the name of the class_name and its related callback_name to the backend program based on the API syntax of each function.
		list_element_url = info[func]['url'].split('/')
		indexes=[i for i,element in enumerate(list_element_url[3:-1]) if element == '(.*)']
		name_classes[func] = "".join([info[func]["inlineVars"][indexes.index(i)].title() if element == '(.*)' else element.title() for i,element in enumerate(list_element_url[3:-1])])
		params_callback[func] = ", ".join([info[func]["inlineVars"][indexes.index(i)] for i,element in enumerate(list_element_url[3:-1]) if element == '(.*)'])

		if (os.path.isfile("funcs_"+restname+"/"+name_classes[func][0].lower()+""+name_classes[func][1:]+"Impl.py")): #if exists, don't create
			print "funcs_"+restname+"/"+name_classes[func][0].lower()+name_classes[func][1:]+"Impl.py already exists, not overwrite"
		else:
			out=open("funcs_"+restname+"/"+name_classes[func][0].lower()+name_classes[func][1:]+"Impl.py","w+")
			out.write(line+line+"class "+name_classes[func]+"Impl :"+line+line)
			index+=1
			'''out.write(tab(index)+"def __init__(self):"+line)
			index+=1
			out.write(tab(index)+"print 'initialize class'"+line+line)
			index-=1'''
			for method in info[func]['methods'].keys():
				out.write(tab(index)+"@classmethod"+line)
				if len (params_callback[func]) > 0:
					out.write(tab(index)+"def "+method+"(cls, "+params_callback[func]+"):"+line)
				else:
					out.write(tab(index)+"def "+method+"(cls):"+line)
				index+=1
				out.write(tab(index)+"print 'handling "+method+"'"+line+line)
				index-=1
			index-=1
			out.close()

if (len(sys.argv)==1):
    print "Filename argument required"
else:
    filename=sys.argv[1]

    #print filename

    file=open(filename, 'rb')

    name=filename.split("/")[-1].split(".")[0]+".py"
    restname=filename.split("/")[-1].split(".")[0].replace("-","_")

    stri=file.read()
    js=json.loads(stri)
    #Translate json into a more manageable structure
    jsret=translateClasses(js)
    #print json.dumps(jsret)
    #generating classes first
    print "Generating Rest Server and Classes for "+name
    print "classes could be found in './objects_"+restname+"/' folder"
    generateClasses(jsret,restname)
    imp=[]
    #create imports for the main class (in case the user needs to use them)
    for klass in jsret:
        imp.append(klass['class'])
    #generate (is any) the RESTful Server
    if "paths" in js.keys():
        jsret2=translateRequest(js)
        ret=generateRESTapi(jsret2,name,imp, restname)
        generateCallableClasses(ret,jsret2,restname)
    print "Finished"




