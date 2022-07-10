import tesrest
import json
import sys
import base64
try:
    with open('config.json') as f:
        cfg = tesrest.AttrDict(json.load(f))
except Exception as ex:
    sys.exit(11)  
try:
    with open(cfg.ENVFILE_MAPPING.strip()) as f:
        envfile_mapping = tesrest.AttrDict(json.load(f))
except Exception as ex:
    sys.exit(11)  

tesconn = tesrest.TESREST(cfg.TIDAL_CM, cfg.CM_USER,base64.b85decode(cfg.CM_PASSWORD).decode('utf-8')) 
res = tesconn.getTESList("Job",f"type = 8 and fullpath like '{tesconn.replaceChars(cfg.JOBGROUP_SELECT)}\\\\*_a'",None,None)
for j in res[0]:
    resultdel = tesconn.updTESObjAction('delete','OSJob',tesconn.dict2Xml('OSJob',j),None)
    print(j.fullpath, resultdel.message)

#id, jobdata =tesconn.getJob(name='', parent = '\\Copy of JDE 9.0\\Australia Grains')
#id, jobdata =tesconn.getJob(name='08:00-20:00 Gen Withhold Certs (R5504A09 PDAR0001)', parent = '\\Copy of JDE 9.0\\Australia Grains')
#id, jobdata =tesconn.getJob(parent = '\\10 As Of ledger posting (R41542 PSAG0008)', name = '')
#id, jobdata =tesconn.getJob(name='', parent = '\\Copy of JDE 9.0\\Australia Grains\\07:15 Australia Grains')
#id, jobdata =tesconn.getJob(name='', parent = '\\Copy of JDE 9.0\\Australia Grains\\07:15 Australia Grains\\10 As Of ledger posting (R41542 PSAG0008)')
print("Done")