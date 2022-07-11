__author__ = 'dkooi'
from email import header
import re
import requests
requests.urllib3.disable_warnings()
import  tesclasses
from requests.auth import HTTPBasicAuth
import datetime
import xml2obj 
import base64
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import logging 
import TESObjects
import json
import urllib.parse
url = ''
user = ''
password = ''
auth = ''
req = ''
s = ''
objectdict = {}
objectdict['hits']=0
objectdict['misses']=0

xmlpost = """\
<?xml version="1.0" encoding="UTF-8" ?>\
<entry xmlns="http://purl.org/atom/ns#">
	<object.function>
		<queryCondition>
        <![CDATA[
#queryCondition
]]>
</queryCondition>
		<selectColumns>#selectColumns</selectColumns>
        <numRows>0</numRows>
	</object.function>
</entry>
"""
xmlpostsorted = """\
<?xml version="1.0" encoding="UTF-8" ?>\
<entry xmlns="http://purl.org/atom/ns#">
	<object.function>
		<queryCondition>#queryCondition</queryCondition>
		<selectColumns>#selectColumns</selectColumns>
        <orderBy>#orderBy</orderBy>
	</object.function>
</entry>
"""

xmlupd = """\
<?xml version="1.0" encoding="UTF-8" ?>\
<entry xmlns="http://purl.org/atom/ns#">\
<object.function xmlns:tes="http://www.tidalsoftware.com/client/tesservlet">\
#obj\
</object.function>\
</entry>
"""
def escape( str ):
    if not  "&amp;" in str:
        str = str.replace("&", "&amp;")
    if not "&lt;" in str:
        str = str.replace("<", "&lt;")
    if not "&gt;" in str: 
        str = str.replace(">", "&gt;")
    if not "&quot;" in str:
        str = str.replace("\"", "&quot;")
    return str

class Py2XML():

    def __init__( self ):

        self.data = "" # where we store the processed XML string

    def parse( self, pythonObj, objName=None ):
        '''
        processes Python data structure into XML string
        needs objName if pythonObj is a List
        '''
        if pythonObj == None:
            return ""

        if isinstance( pythonObj, dict ):
            self.data = self._PyDict2XML( pythonObj )

        elif isinstance( pythonObj, list ):
            # we need name for List object
            self.data = self._PyList2XML( pythonObj, objName )

        else:
            self.data = "<%(n)s>%(o)s</%(n)s>" % { 'n':objName, 'o':str( pythonObj ) }

        return self.data

    def _PyDict2XML( self, pyDictObj, objName=None ):
        '''
        process Python Dict objects
        They can store XML attributes and/or children
        '''
        tagStr = ""     # XML string for this level
        attributes = {} # attribute key/value pairs
        attrStr = ""    # attribute string of this level
        childStr = ""   # XML string of this level's children

        for k, v in pyDictObj.items():

            if isinstance( v, dict ):
                # child tags, with attributes
                childStr += self._PyDict2XML( v, k )

            elif isinstance( v, list ):
                # child tags, list of children
                childStr += self._PyList2XML( v, k )

            else:
                # tag could have many attributes, let's save until later
                attributes.update( { k:v } )

        if objName == None:
            return childStr

        # create XML string for attributes
        for k, v in attributes.items():
            attrStr += " %s=\"%s\"" % ( k, v )

        # let's assemble our tag string
        if childStr == "":
            tagStr += "<%(n)s%(a)s />" % { 'n':objName, 'a':attrStr }
        else:
            tagStr += "<%(n)s%(a)s>%(c)s</%(n)s>" % { 'n':objName, 'a':attrStr, 'c':childStr }

        return tagStr

    def _PyList2XML( self, pyListObj, objName=None ):
        '''
        process Python List objects
        They have no attributes, just children
        Lists only hold Dicts or Strings
        '''
        tagStr = ""    # XML string for this level
        childStr = ""  # XML string of children

        for childObj in pyListObj:

            if isinstance( childObj, dict ):
                # here's some Magic
                # we're assuming that List parent has a plural name of child:
                # eg, persons > person, so cut off last char
                # name-wise, only really works for one level, however
                # in practice, this is probably ok
                childStr += self._PyDict2XML( childObj, objName[:-1] )
            else:
                for string in childObj:
                    childStr += string;

        if objName == None:
            return childStr

        tagStr += "<%(n)s>%(c)s</%(n)s>" % { 'n':objName, 'c':childStr }

        return tagStr

class TESREST:
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        if type(password) is str:
            self.password = password
        else:
            self.password = base64.b85decode(password).decode('utf-8')
            print(self.password)
        self.auth = HTTPBasicAuth(self.user, self.password)
        self.s = requests.Session()
        self.req = requests.Request('GET', self.url, auth=self.auth)
        prepped = self.req.prepare()
        self.resp = self.s.send(prepped, verify=False)
        self.jobruncommand = """<?xml version="1.0" encoding="UTF-8"?> 
    <entry xmlns=""http://purl.org/atom/ns#"">
    <id>#id/id>
    <tes:JobRun.#function xmlns:tes="http://www.tidalsoftware.com/client/tesservlet">
        #value
    </tes:JobRun.rerun>
    </entry>
    """
        if not self.resp.ok:
            print(f"Not Connected: {self.resp}")
        else:
            print("Connected to CM")

    def connect(self, url, user, password):
        return self.__init__(self, url, user, password)

    def getNodeList(self):
        if self.req is None:
            raise Exception('Not connected to TES')
        self.req = s.Request('GET', self.url + '/Node.getList', auth=self.auth)
        prepped = self.req.prepare()
        self.resp = self.s.send(prepped,verify=False)
        # print self.resp.text
        r2 = re.sub(' xmlns="[^"]+"', '', self.resp.text)
        root = ET.fromstring(r2)
        # feed= root.find('feed')
        el2 = root.findall(".//node")
        nodeList = []
        ET.register_namespace('', 'http://www.tidalsoftware.com/client/tesservlet')
        for entry in root.iter('entry'):
            for node in entry.iter('{http://www.tidalsoftware.com/client/tesservlet}node'):
                nodeList.append(xml2obj.xml2obj(ET.tostring(node)))
        return nodeList
    def getOutputContent(self,jobid):
        if self.req is None:
            raise Exception('Not connected to TES')
        self.req = s.Request('GET', self.url + '/OutputContent.getList', auth=self.auth)
        prepped = self.req.prepare()
        self.resp = self.s.send(prepped,verify=False)
        # print self.resp.text
        r2 = re.sub(' xmlns="[^"]+"', '', self.resp.text)
        root = ET.fromstring(r2)
        # feed= root.find('feed')
        el2 = root.findall(".//node")
        nodeList = []
        ET.register_namespace('', 'http://www.tidalsoftware.com/client/tesservlet')
        for entry in root.iter('entry'):
            for node in entry.iter('{http://www.tidalsoftware.com/client/tesservlet}node'):
                nodeList.append(xml2obj.xml2obj(ET.tostring(node)))
        return nodeList

    def deleteTes(self,objectname, criteria, logger=None):
        newxml = xmlupd.replace('object', objectname).replace('function', 'delete').replace('#obj', criteria).replace('\n','').replace('\t','')
        data = {'data':{newxml}}
        headers={}
        self.req = requests.Request('POST',self.url + '/post',  data=data,headers=headers, auth=self.auth)
        prepped = self.s.prepare_request(self.req)
        start_time = datetime.datetime.now()
        self.resp = self.s.send(prepped,verify=False)
        elapsed = datetime.datetime.now() - start_time
        mes = "Elapsed time %d " % elapsed.seconds
        root = ET.fromstring(self.resp.text.encode('utf-8'))
        objlist = []
        tesobjlist = []
        ET.register_namespace('', 'http://www.tidalsoftware.com/client/tesservlet')
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}' + objectname.lower()):
            xml = ET.tostring(entry)
            obji = xml2obj.xml2obj(xml,objectname)
            if len(obji._attrs) > 1:
                obji._attrs['TESObject'] = objectname
                objlist.append(obji)
        if len(tesobjlist) > 0:
            return (tesobjlist, mes + ':' + newxml)
        return (objlist, mes + ':' + newxml)


    def getTESList(self,objectname, criteria, columns=None, logger=None):
        if self.req is None:
            raise Exception('Not </tes:  + keto TES')
        from http.client import HTTPConnection  # py3
        #print(criteria)
        #HTTPConnection.debuglevel = 2 
        #           
        newxml = xmlpost.replace('object', objectname).replace('function', 'getList').replace('#queryCondition', criteria).replace('#selectColumns', columns if columns != None else '').replace('\n','').replace('\t','')
        #print(newxml)
        #newxml = """<?xml version="1.0" encoding="UTF-8" ?><entry xmlns="http://purl.org/atom/ns#">	<Job.getList>		<queryCondition>fullPath = '\\10 As Of ledger posting \(R41542  PSAG0008\)'</queryCondition>		<selectColumns/>		<numRows>1</numRows>	</Job.getList></entry>"""
        data = {'data':{newxml}}
        #data = "data:" + urllib.parse.quote(newxml,safe='\\')
        #headers= { 'Content-Type' : 'application/x-www-form-urlencoded'}
        #headers={'Content-Type' : 'text/plain'}
        #headers={'Content-Type' : 'multipart/form-data'}
        #headers={'Content-Type' : 'text/xml;charset=utf-8'}
        headers={}
        #data = f"data:{newxml}"
        self.req = requests.Request('POST',self.url + '/post',  data=data,headers=headers, auth=self.auth)
        prepped = self.s.prepare_request(self.req)
        start_time = datetime.datetime.now()
        self.resp = self.s.send(prepped,verify=False)
        elapsed = datetime.datetime.now() - start_time
        mes = "Elapsed time %d " % elapsed.seconds
        
        # r2 = re.sub(' xmlns="[^"]+"', '', self.resp.text)
        # root = ET.fromstring(r2)
        root = ET.fromstring(self.resp.text.encode('utf-8'))
        objlist = []
        tesobjlist = []
        ET.register_namespace('', 'http://www.tidalsoftware.com/client/tesservlet')
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}' + objectname.lower()):
            #            python_object = deserializer.parse(ET.tostring(entry))
            xml = ET.tostring(entry)
            obji = xml2obj.xml2obj(xml,objectname)
            #if objectname == 'Variable':
            #    tesobjlist.append(Variable(obji["id"],obji["name"],obji["innervalue"],obji["pub"],obji["publish"],obji["readonly"],obji["ownerid"],obji["description"],obji["type"]))
            #if objectname == 'JobRun':
            if len(obji._attrs) > 1:
                obji._attrs['TESObject'] = objectname
                objlist.append(obji)
        if len(tesobjlist) > 0:
            return (tesobjlist, mes + ':' + newxml)
        return (objlist, mes + ':' + newxml)

    def getCalendarForecast(self,calendarid):
        try:
            #calid = self.getCalendarId(calendarname)
            result = self.getTESFunctionResult(objectname= "CalendarYear",function= "getForecast",  criteria= f"<calendarid>{calendarid}</calendarid>")        
            forecastdates = result.split(',')
            return forecastdates
        except Exception as ex:
            print(ex)
            return None

    def getTESFunctionResult(self,objectname,function, criteria, columns=None, logger=None):
        try:
            if self.req is None:
                raise Exception('Not </tes:  + keto TES')
            newxml = xmlupd.replace('object', objectname).replace('function', function).replace('#obj', criteria).replace('#selectColumns', columns if columns != None else '').replace('\n','').replace('\t','')
            data = {'data': newxml}
            self.req = requests.Request('POST',self.url + '/post', data=data, auth=self.auth)
            prepped = self.s.prepare_request(self.req)
            self.resp = self.s.send(prepped,verify=False)
            pattern = "<tes:message>(.*?)</tes:message>"
            substring = re.search(pattern, self.resp.text).group(1)
        except Exception as ex:
            substring =''
        return substring


    def getObjectidByName(self,object,name):
        if f"{object}_{name}" in objectdict:
            objectdict['hits'] +=1
            return objectdict[f"{object}_{name}"]
        r1 = self.getTESList(object, f"lower(name)='{name.lower()}'")
        objectdict['misses'] +=1
        if len(r1[0])!= 1:
            return -1
        else:
            objectdict[f"{object}_{name}"] = r1[0][0].id
            return r1[0][0].id
    def getObjectById(self,object,id):
        if f"{object}_{id}" in objectdict:
            objectdict['hits'] +=1
            return objectdict[f"{object}_{id}"]
        r1 = self.getTESList(object, f"id='{id}'")
        objectdict['misses'] +=1
        if len(r1[0])!= 1:
            return -1
        else:
            objectdict[f"{object}_{id}"] = r1[0][0]
            return r1[0][0]

    def getTESListSorted(self,objectname, criteria, columns=None, orderBy=None):
        if self.req is None:
            raise Exception('Not </tes:  + keto TES')
        newxml = xmlpostsorted.replace('object', objectname).replace('function', 'getList').replace('#queryCondition', criteria).replace('#orderBy', orderBy if orderBy != None else '').replace('#selectColumns', columns if columns != None else '').replace('\n','').replace('\t','')
        data = {'data': newxml}
        self.req = requests.Request('POST',self.url + '/post', data=data, auth=self.auth)
        prepped = self.s.prepare_request(self.req)
        start_time = datetime.datetime.now()
        self.resp = self.s.send(prepped,verify=False)
        elapsed = datetime.datetime.now() - start_time
        mes = "Elapsed time %d " % elapsed.seconds
        
        # r2 = re.sub(' xmlns="[^"]+"', '', self.resp.text)
        # root = ET.fromstring(r2)
        root = ET.fromstring(self.resp.text.encode('utf-8'))
        objlist = []
        tesobjlist = []
        ET.register_namespace('', 'http://www.tidalsoftware.com/client/tesservlet')
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}' + objectname.lower()):
            #            python_object = deserializer.parse(ET.tostring(entry))
            xml = ET.tostring(entry)
            obji = xml2obj.xml2obj(xml,objectname)
            if len(obji._attrs) > 1:
                obji._attrs['TESObject'] = objectname
                objlist.append(obji)
        if len(tesobjlist) > 0:
            return (tesobjlist, mes + ':' + newxml)
        return (objlist, mes + ':' + newxml)
        
    def getJobbyName(self,name):
        tname = self.replaceChars(name)
        #tname=  name.replace('(','\\(').replace(')','\\)').replace(',','\\,').replace('=','\\=')     
        results = self.getTESList("Job",f"job.name = '{tname}'",None,logging)    
        if len(results[0]) == 1:
            jobid = results[0][0]['id']
            newjob = results[0][0]
        else:
            jobid = None
            newjob = xml2obj.xml2obj(TESObjects.Job,'job')
            newjob['name'] = name
            newjob['parentname'] = ''
        return jobid, newjob

    def getJobbyId(self,id):
        results = self.getTESList("Job",f"job.id = '{id}'",None,logging)    
        if len(results[0]) == 1:
            jobid = results[0][0]['id']
            newjob = results[0][0]
        else:
            jobid = None
            newjob = xml2obj.xml2obj(TESObjects.Job,'job')
            newjob['name'] = id
            newjob['parentname'] = ''
        return jobid, newjob

    def getJobbyAlias(self,alias):
        results = self.getTESList("Job",f"job.alias = '{alias}'",None,logging)    
        if len(results[0]) == 1:
            jobid = results[0][0]['id']
            newjob = results[0][0]
        else:
            jobid = None
            newjob = xml2obj.xml2obj(TESObjects.Job,'job')
            newjob['name'] = ''
            newjob['parentname'] = ''
        return jobid, newjob
        
    def getAllJobsbyName(self,name):
        tname=  name.replace('(','\\(').replace(')','\\)').replace(',','\\,').replace('=','\\=')
        results = self.getTESList("Job",f"job.name = '{tname}'",None,logging)    
        return results[0]
    def replaceChars(self,name):
        _strs = '\\,*?()\'!=<>'
        for x in _strs:
            name = name.replace(x,"\\" + x)
        return name
        #return name.replace('(','\\(').replace(')','\\)').replace(',','\\,').replace('=','\\=').replace("'","\\'").replace("<","\\<").replace(">","\\>")

    def getJob(self,name,parent, cached=True):
        '''
        r'*?(),\'!=<>'
        '''        
        if cached:
            if f"job_{name}_{parent}" in objectdict:
                objectdict['hits'] +=1
                return objectdict[f"job_{name}_{parent}"]['id'],objectdict[f"job_{name}_{parent}"]
            else:
                objectdict['misses'] +=1
        else:
            try:
                del objectdict[f"job_{name}_{parent}"]
            except Exception as ex:
                pass
        
        #parent = parent.replace('\\','\\\\') 
        tname=    self.replaceChars(name)   #.replace('(','\\(').replace(')','\\)').replace(',','\\,').replace('=','\\=').replace("'","\\'").replace("<","\\<").replace(">","\\>")            
        tparent= self.replaceChars(parent)                     #.replace('(','\\(').replace(')','\\)').replace(',','\\,').replace('=','\\=').replace("'","\\'").replace("<","\\<").replace(">","\\>")
            #if cfg.API_VERSION=='6.3':
            #    tparent = '\\' + tparent.strip('\\') 
        if tname == None or tname == '':
            results = self.getTESList("Job",f"job.fullPath like '{tparent}'",None,logging)
        else:
            if tparent == '':
                results = self.getTESList("Job",f"job.parentname is Null and job.name = '{tname}'",None,logging)
            else:
                if '*' in tparent:
                    results = self.getTESList("Job",f"job.parentname like '{tparent}' and job.name = '{tname}'",None,logging)
                else:
                    results = self.getTESList("Job",f"job.parentname like '{tparent}' and job.name like '{tname}'",None,logging)

        if len(results[0]) == 1:
            jobid = results[0][0]['id']
            newjob = results[0][0]
            if newjob['typename'] =='FTPJOB':
                id = newjob['id']
                results = self.getTESList("FTPJob",f"job.id = '{id}'",None,logging)
                newjob = results[0][0]
                #newjob = xml2obj.xml2obj(TESObjects.FTPJob,'FTPJob')

            if cached:
                objectdict[f"job_{name}_{parent}"] = results[0][0]
        else:
            jobid = None
            #logging.info('Not found', name, parent)
            newjob = xml2obj.xml2obj(TESObjects.Job,'job')
            if newjob['typename'] =='FTPJOB':
                newjob = xml2obj.xml2obj(TESObjects.FTPJob,'ftpjob')
            newjob['name'] = name
            newjob['parentname'] = parent
        return jobid, newjob

    def getCalendarId(self,name):
        if name =='':
            return -1
        if name != name.replace('(','\\(').replace(')','\\)').replace(',','\\,').replace ('&','&amp;'):
            pass
        name = name.replace('(','\\(').replace(')','\\)').replace(',','\\,').replace ('&','&amp;')
        r1 = self.getTESList("Calendar", f"name='{name.strip()}'")
        if len(r1[0]) == 1:
            return  r1[0][0]['id']            
        else:
            r1 = self.getTESList("Calendar", f"lower(name)='{name.strip().lower()}'")
            if len(r1[0]) == 1:
                return  r1[0][0]['id']
            else:
                logging.info(f'Calendar not found 2 {name}')
                return -1
    def getRuntimeUser(self,rtu):
            if rtu.find('\\')> -1:
                domain , name = rtu.split('\\')
                to_r = self.getTESList("Users", f"upper(name)='{name.upper()}' and upper(domain)='{domain.upper()}'")    
            else:
                to_r = self.getTESList("Users", f"upper(name)='{rtu.upper()}' and domain is null")
            if len(to_r[0]) == 1:
                objectdict[f"Users_{rtu}"] = to_r[0][0]['id']
                return  to_r[0][0]['id']
            else:
                if rtu.find('\\')> -1:
                    domain , name = rtu.split('\\')
                    to_r = self.getTESList("Users", f"upper(name)='{name.upper()}' and upper(domain)='{domain.upper()}'")    
                else:
                    to_r = self.getTESList("Users", f"upper(name)='{rtu.upper()}' and domain is null")
                if len(to_r[0]) == 1:
                    objectdict[f"Users_{rtu}"] = to_r[0][0]['id']
                    return  to_r[0][0]['id']
                else:
                    return -1

    def getAgentid(self,name):
        r1 = self.getTESList("Node", f"upper(name)='{name.upper()}'")
        if len(r1[0])== 0:
            return -1
        else:
            return r1[0][0].id
    def getAgentidByMachine(self,name, servicename):
        r1 = self.getTESList("Node", f"upper(machine)='{name.upper()}' and upper(servicename) = '{servicename.upper()}'")
        if len(r1[0])== 0:
            return -1
        else:
            return r1[0][0].id



    def TESLogout(self):
        newxml = xmlpost.replace('object', 'Users').replace('function', 'logoutSession').replace('#queryCondition', '')
        data = {'data': newxml}
        self.req = requests.Request('POST', self.url + '/post', data=data, auth=self.auth)
        prepped = self.req.prepare()
        self.resp = self.s.send(prepped,verify=False)

    def __del__(self):

        #print('Objectdict hits',objectdict['hits'])
        #print('Objectdict misses',objectdict['misses'])
        if False:
            newxml = xmlpost.replace('object', 'Users').replace('function', 'logoutSession').replace('#queryCondition', '')
            data = {'data': newxml}
            self.req = requests.Request('POST', self.url + '/post', data=data, auth=self.auth)
            prepped = self.s.prepare_request(self.req)
            self.resp = self.s.send(prepped,verify=False)

    def dict2Xml(self, objectname, obj):
        if  obj['variables']:
            obj['variables'] = obj['variables'].replace("<name>", "<variables:name>").replace("</name>", "</variables:name>").replace("<row>", "<variables:row>").replace("</row>", "</variables:row>").replace("<value>", "<variables:value>").replace("</value>", "</variables:value>").replace("<id>", "<variables:id>").replace("</id>", "</variables:id>")
        xml = "<" + objectname + ' xmlns:tes="http://www.tidalsoftware.com/client/tesservlet" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        try:
            for key, val in obj._attrs.items():
                if type(val) == str:
                    if key in ['extendedinfo','parameters','variables']:
                        if val != None:                    
                            xml += "<tes:" + key + ">" + escape(val) + "</tes:" + key + ">" 
                    else:
                            xml += "<tes:" + key + ">" + escape(val) + "</tes:" + key + ">" 
                else:
                    pass
            xml += "</" + objectname + ">"
        except:
            for key, val in obj.items():
                if type(val) == str:
                    if key in ['extendedinfo','parameters','variables']:
                        if val != None:                    
                            xml += "<tes:" + key + ">" + escape(val) + "</tes:" + key + ">" 
                    else:
                            xml += "<tes:" + key + ">" + escape(val) + "</tes:" + key + ">" 
                else:
                    pass
            xml += "</" + objectname + ">"
        return xml


    def updTESObj(self,  function,objname, obj, logger):
        """
        :rtype: Result
        """
        if self.req is None:
            raise Exception('Not connected to TES')
        if 'typename' in obj._attrs:
            if obj._attrs['typename'].lower() =='jobgroup':
                obj.TESObject = 'JobGroup'
                obj._attrs.pop('command', None)
            if obj._attrs['typename'].lower() =='job':
                obj.TESObject = 'Job'
            if obj._attrs['typename'].lower() =='jobrun':
                obj.TESObject = 'JobRun'
            if obj._attrs['typename'].lower() =='servicejob':
                obj.TESObject = 'ServiceJob'
            if obj._attrs['typename'].lower() =='ftpjob':
                obj.TESObject = 'FTPJob'
            if obj._attrs['typename'].lower() =='osjob':
                obj.TESObject = 'OSJob'
        else:
            if obj.TESObject.lower() =='job':
                if obj.type == '8':
                    obj.TESObject = 'ServiceJob'
                if obj.type == '6':
                    obj.TESObject = 'FTPJob'
                if obj.type == '1':
                    obj.TESObject = 'JobGroup'
                if obj.type == '2':
                    obj.TESObject = 'Job'
        if isinstance(obj,str):
            newxml = xmlupd.replace('object', objname).replace('function', function).replace('#obj',str(obj))
        else:
            newxml = xmlupd.replace('object', objname).replace('function', function).replace('#obj',self.dict2Xml(objname,obj))
        data = {'data': newxml.replace('\n','').replace('\t','')}
        if logger != None:
            logger.debug(data['data'])
        headers = {'Content-Type': 'application/atom xml'}
        self.req = requests.Request('POST', self.url + '/post', data=data, auth=self.auth)
        prepped = self.s.prepare_request(self.req)
        self.resp = self.s.send(prepped,verify=False)
        # r2 = re.sub(' xmlns="[^"]+"', '', self.resp.text)
        # root = ET.fromstring(r2)
        root = ET.fromstring(self.resp.text)
        if logger != None:
            logger.debug(self.resp.text)
        result = tesclasses.Result
        result.message = f" {self.resp.status_code} {self.resp.reason}"
        ET.register_namespace('', 'http://www.tidalsoftware.com/client/tesservlet')
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}operation'):
            result.operation = entry.text
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}ok'):
            result.ok = entry.text
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}message'):
            result.message = entry.text
        return result

    def updTESObjAction(self,  function, objname,content,logger):
        """
        :rtype: Result
        """
        if self.req is None:
            raise Exception('Not connected to TES')
        if isinstance(content,tesclasses.TESObject):
            serializer = Py2XML()
            newxml = xmlupd.replace('object', objname).replace('function', function).replace('#obj',str(content))
        else:
            newxml = xmlupd.replace('object', objname).replace('function', function).replace('#obj',content)
        #data = {'data': newxml.replace('\n','').replace('\t','')}
        data = {'data': newxml.rstrip('\n')}
        if logger != None:
            logger.debug(newxml)
        #else:
        #    print(newxml)
        headers = {'Content-Type': 'application/atom xml'}
        self.req = requests.Request('POST', self.url + '/post', data=data, auth=self.auth)
        prepped = self.s.prepare_request(self.req)
        self.resp = self.s.send(prepped,verify=False)
        # r2 = re.sub(' xmlns="[^"]+"', '', self.resp.text)
        # root = ET.fromstring(r2)
        result = tesclasses.Result()
        #result.message = s
        root = ET.fromstring(self.resp.text)
        if logger != None:
            logger.debug(self.resp.text)
        result.message = f" {self.resp.status_code} {self.resp.reason}"
        ET.register_namespace('', 'http://www.tidalsoftware.com/client/tesservlet')
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}operation'):
            result.operation += entry.text
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}ok'):
            result.ok += entry.text
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}message'):
            result.message += ' ' + entry.text
        
        return result


    def JobRunCommand(self, function, obj):
        """
        :rtype: Result
        """
        if self.req is None:
            raise Exception('Not connected to TES')
        if isinstance(obj,tesclasses.TESObject):
            serializer = Py2XML()
            newxml = xmlupd.replace('object', obj.TESObject).replace('function', function).replace('#obj',str(obj))
        else:
            newxml = xmlupd.replace('object', obj.TESObject).replace('function', function).replace('#obj',self.dict2Xml(obj.TESObject,obj))
        data = {'data': newxml}
        headers = {'Content-Type': 'application/atom xml'}
        self.req = requests.Request('POST', self.url + '/post', data=data, auth=self.auth)
        prepped = self.s.prepare_request(self.req)
        self.resp = self.s.send(prepped,verify=False)
        # r2 = re.sub(' xmlns="[^"]+"', '', self.resp.text)
        # root = ET.fromstring(r2)
        root = ET.fromstring(self.resp.text)
        result = tesclasses.Result()
        ET.register_namespace('', 'http://www.tidalsoftware.com/client/tesservlet')
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}operation'):
            result.operation = entry.text
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}ok'):
            result.ok = entry.text
        for entry in root.iter('{http://www.tidalsoftware.com/client/tesservlet}message'):
            result.message = entry.text
        return result

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class Py2XML():

    def __init__( self ):

        self.data = "" # where we store the processed XML string

    def parse( self, pythonObj, objName=None ):
        '''
        processes Python data structure into XML string
        needs objName if pythonObj is a List
        '''
        if pythonObj == None:
            return ""

        if isinstance( pythonObj, dict ):
            self.data = self._PyDict2XML( pythonObj )

        elif isinstance( pythonObj, list ):
            # we need name for List object
            self.data = self._PyList2XML( pythonObj, objName )

        else:
            self.data = "<%(n)s>%(o)s</%(n)s>" % { 'n':objName, 'o':str( pythonObj ) }

        return self.data

    def _PyDict2XML( self, pyDictObj, objName=None ):
        '''
        process Python Dict objects
        They can store XML attributes and/or children
        '''
        tagStr = ""     # XML string for this level
        attributes = {} # attribute key/value pairs
        attrStr = ""    # attribute string of this level
        childStr = ""   # XML string of this level's children

        for k, v in pyDictObj.items():

            if isinstance( v, dict ):
                # child tags, with attributes
                childStr += self._PyDict2XML( v, k )

            elif isinstance( v, list ):
                # child tags, list of children
                childStr += self._PyList2XML( v, k )

            else:
                # tag could have many attributes, let's save until later
                attributes.update( { k:v } )

        if objName == None:
            return childStr

        # create XML string for attributes
        for k, v in attributes.items():
            attrStr += " %s=\"%s\"" % ( k, v )

        # let's assemble our tag string
        if childStr == "":
            tagStr += "<%(n)s%(a)s />" % { 'n':objName, 'a':attrStr }
        else:
            tagStr += "<%(n)s%(a)s>%(c)s</%(n)s>" % { 'n':objName, 'a':attrStr, 'c':childStr }

        return tagStr

    def _PyList2XML( self, pyListObj, objName=None ):
        '''
        process Python List objects
        They have no attributes, just children
        Lists only hold Dicts or Strings
        '''
        tagStr = ""    # XML string for this level
        childStr = ""  # XML string of children

        for childObj in pyListObj:

            if isinstance( childObj, dict ):
                # here's some Magic
                # we're assuming that List parent has a plural name of child:
                # eg, persons > person, so cut off last char
                # name-wise, only really works for one level, however
                # in practice, this is probably ok
                childStr += self._PyDict2XML( childObj, objName[:-1] )
            else:
                for string in childObj:
                    childStr += string;

        if objName == None:
            return childStr

        tagStr += "<%(n)s>%(c)s</%(n)s>" % { 'n':objName, 'c':childStr }

        return tagStr

        
