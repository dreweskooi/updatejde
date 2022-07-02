
class TESObject:
    def __init__(self):
        self.id = None
        self.name = None
        self.objectname = None
        self.TESObject = ''
    def __str__(self):
        strdata ="<tes:" + self.TESObject + ">"
        members = [attr for attr in dir(self) if not callable(attr) and not attr.startswith("__")]
        for f in members:
            value =  getattr(self,f)
            null =''
            if value == None:
                value=''
                null = ' tes:null="Y"'
            strdata += '<tes:' + f + null + '>' + value + '</tes:' + f + '>'
        strdata +="</tes:" + self.TESObject + ">"
        return strdata

class Job(TESObject):
        def __init__(self):
            self.TESObject ='Job'

class JobRun(TESObject):
        def __init__(self):
            self.TESObject ='JobRun'

class Result:
    def __init__(self):
        self.result=''
        self.message =''
        self.operation =''
        self.ok =''

class Variable(TESObject):
    def __init__(self,id, name, innervalue,pub,publish, readonly,ownerid,description,type):
        self.id = id
        self.name = name
        self.innervalue = innervalue
        self.pub = pub
        self.publish = publish
        self.readonly = readonly
        self.ownerid = ownerid
        self.TESObject ='Variable'
        self.description = description
        self.type = type

