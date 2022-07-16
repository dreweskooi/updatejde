from modulefinder import ReplacePackage
import tesrest
import json
import sys
import base64
import re
"""This script will update jde jobs create by jde sc conversion to enable or disable and delete sc jobs

    Parameters: 
    argument1 (string): functions:
                        delete : will delete all jde adapter jobs that macth selection criteria and end with cfg.NEWJOB_EXTENSION (_A)
                        jde_enable: will disable sc job and enable corresponding adapter job
                        jde_disable: will disable jde apterjob and enable sc job
                        scjob_delete: will delete sc job

    Returns:
    exit code 

   """
valid_options = ['delete' , 'jdejob_enable', 'jdejob_disable','scjob_delete', 'check_added_jde_job_deps']
if len(sys.argv) != 2 or len(sys.argv) ==2 and not sys.argv[1] in valid_options :
    print(f"Valid option required : {valid_options}  !") 
    sys.exit(1)
try:
    with open('config.json') as f:
        cfg = tesrest.AttrDict(json.load(f))
except Exception as ex:
    print("Error opening config.json : ",ex)
    sys.exit(11)  
try:
    with open(cfg.ENVFILE_MAPPING.strip()) as f:
        envfile_mapping = tesrest.AttrDict(json.load(f))
except Exception as ex:
    print("Error opening envfile_maping file : ",ex)
    sys.exit(11)  
print(f"{sys.argv[1]} option selected")
tesconn = tesrest.TESREST(cfg.TIDAL_CM, cfg.CM_USER,base64.b85decode(cfg.CM_PASSWORD).decode('utf-8')) 
if sys.argv[1] == 'delete':
    res = tesconn.getTESList("Job",f"type = 8 and fullpath like '{tesconn.replaceChars(cfg.JOBGROUP_SELECT)}\\\\*{cfg.NEWJOB_EXTENSION}'",None,None)
    for j in res[0]:
        resultdel = tesconn.updTESObjAction('delete','OSJob',tesconn.dict2Xml('OSJob',j),None)
        print(j.fullpath, resultdel.message)
if sys.argv[1] == 'jdejob_enable':
    res = tesconn.getTESList("Job",f"type = 8 and fullpath like '{tesconn.replaceChars(cfg.JOBGROUP_SELECT)}\\\\*{cfg.NEWJOB_EXTENSION}'",None,None)
    for j in res[0]:
        job_id, jobdata = tesconn.getJob('', re.sub( tesconn.replaceChars(cfg.NEWJOB_EXTENSION) + '$', '', j['fullpath']))
        if job_id != None:
            if jobdata['active']=='Y':
                jobdata['active'] ='N'
                result = tesconn.updTESObjAction('update','OSJob',tesconn.dict2Xml('OSJob',jobdata),None)
                print(jobdata.fullpath, result.message)
                j['active'] ='Y'
                result = tesconn.updTESObjAction('update','ServiceJob',tesconn.dict2Xml('OSJob',j),None)
                print(j.fullpath, result.message)
if sys.argv[1] == 'jdejob_disable':
    res = tesconn.getTESList("Job",f"type = 8 and fullpath like '{tesconn.replaceChars(cfg.JOBGROUP_SELECT)}\\\\*{cfg.NEWJOB_EXTENSION}'",None,None)
    for j in res[0]:
        job_id, jobdata = tesconn.getJob('', re.sub( tesconn.replaceChars(cfg.NEWJOB_EXTENSION) + '$', '', j['fullpath']))
        if job_id != None:
            if jobdata['active']=='Y':
                jobdata['active'] ='N'
                result = tesconn.updTESObjAction('update','OSJob',tesconn.dict2Xml('OSJob',jobdata),None)
                print(jobdata.fullpath, result.message)
                j['active'] ='Y'
                result = tesconn.updTESObjAction('update','ServiceJob',tesconn.dict2Xml('OSJob',j),None)
                print(j.fullpath, result.message)
if sys.argv[1] == 'scjob_delete':
    res = tesconn.getTESList("Job",f"type = 8 and fullpath like '{tesconn.replaceChars(cfg.JOBGROUP_SELECT)}\\\\*{cfg.NEWJOB_EXTENSION}'",None,None)
    for j in res[0]:
        j['active'] ='Y'
        result = tesconn.updTESObjAction('update','ServiceJob',tesconn.dict2Xml('OSJob',j),None)
        print(j.fullpath, result.message)
        job_id, jobdata = tesconn.getJob('', re.sub( tesconn.replaceChars(cfg.NEWJOB_EXTENSION) + '$', '', j['fullpath']))
        if job_id != None:
            result = tesconn.updTESObjAction('delete','OSJob',tesconn.dict2Xml('OSJob',jobdata),None)
            print(jobdata.fullpath, result.message)
if sys.argv[1] == 'check_added_jde_job_deps':
    rjobdep = tesconn.getTESList(f"JobDependency","id>0")
    rjobdep[0].sort(key=lambda x: (x.jobid, x.depjobparent,x.depjobname))
    print("Check following jobs for dependency issues")
    for r in rjobdep[0]:
        if r.depjobname.endswith(cfg.NEWJOB_EXTENSION) and r.depjobtype == '8':
            #_t = re.sub( tesconn.replaceChars(cfg.NEWJOB_EXTENSION) + '$', '', r.depjobname)
            # filter where jobid are the ame , dep parent same, ad depjobname = 
            deps = filter(lambda x: x.jobid == r.jobid and  x.depjobparent== r.depjobparent and  x.depjobname ==  re.sub( tesconn.replaceChars(cfg.NEWJOB_EXTENSION) + '$', '', r.depjobname),   rjobdep[0])
            for d in deps:
                print(d.jobid, d.jobname, d.depjobname, d.depjobparent)

        #print(r)

#id, jobdata =tesconn.getJob(name='', parent = '\\Copy of JDE 9.0\\Australia Grains')
#id, jobdata =tesconn.getJob(name='08:00-20:00 Gen Withhold Certs (R5504A09 PDAR0001)', parent = '\\Copy of JDE 9.0\\Australia Grains')
#id, jobdata =tesconn.getJob(parent = '\\10 As Of ledger posting (R41542 PSAG0008)', name = '')
#id, jobdata =tesconn.getJob(name='', parent = '\\Copy of JDE 9.0\\Australia Grains\\07:15 Australia Grains')
#id, jobdata =tesconn.getJob(name='', parent = '\\Copy of JDE 9.0\\Australia Grains\\07:15 Australia Grains\\10 As Of ledger posting (R41542 PSAG0008)')
print("Done")