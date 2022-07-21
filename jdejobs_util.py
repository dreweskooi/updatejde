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
try:
    with open('config.json') as f:
        cfg = tesrest.AttrDict(json.load(f))
except Exception as ex:
    print("Error opening config.json : ",ex)
    sys.exit(11)  
valid_options = ['delete_added_jdejobs' , 'jdejob_enable', 'jdejob_disable','scjob_delete', 'check_added_jde_job_deps']
if len(sys.argv) != 2 or len(sys.argv) ==2 and not sys.argv[1] in valid_options and (not sys.argv[1].isnumeric() and sys.argv[1] < len(valid_options)) :
    print(f"Specify one of these options : {valid_options}  !") 
    for x,y in enumerate(valid_options):
        print(x,'=',y)
    print(f"Current group selected is: {cfg.JOBGROUP_SELECT}")
    sys.exit(1)
try:
    with open(cfg.ENVFILE_MAPPING.strip()) as f:
        envfile_mapping = tesrest.AttrDict(json.load(f))
except Exception as ex:
    print("Error opening envfile_maping file : ",ex)
    sys.exit(11)  
if sys.argv[1].isnumeric():
    print(f"{sys.argv[1]}={valid_options[int(sys.argv[1])]}  selected")
else:
    print(sys.argv[1], " selected")
print(f"Using this group to select jobs to check: {cfg.JOBGROUP_SELECT}")
tesconn = tesrest.TESREST(cfg.TIDAL_CM, cfg.CM_USER,base64.b85decode(cfg.CM_PASSWORD).decode('utf-8')) 
if sys.argv[1] == valid_options[0]  or sys.argv[1] == '0':  #'delete_added_jdejobs'
    #print(valid_options[int(sys.argv[1])])
    res = tesconn.getTESList("Job",f"type = 8 and fullpath like '{tesconn.replaceChars(cfg.JOBGROUP_SELECT)}\\\\*{cfg.NEWJOB_EXTENSION}'",None,None)
    for j in res[0]:
        resultdel = tesconn.updTESObjAction('delete','OSJob',tesconn.dict2Xml('OSJob',j),None)
        print(j.fullpath, resultdel.message)
if sys.argv[1] == valid_options[1]  or sys.argv[1] == '1': #sys.argv[1] == 'jdejob_enable':
    #print(valid_options[int(sys.argv[1])])
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
if sys.argv[1] == valid_options[2]  or sys.argv[1] == '2': #if sys.argv[1] == 'jdejob_disable':
    #print(valid_options[int(sys.argv[1])])
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
if sys.argv[1] == valid_options[3]  or sys.argv[1] == '3': #sys.argv[1] == 'scjob_delete':
    res = tesconn.getTESList("Job",f"type = 8 and fullpath like '{tesconn.replaceChars(cfg.JOBGROUP_SELECT)}\\\\*{cfg.NEWJOB_EXTENSION}'",None,None)
    for j in res[0]:
        j['active'] ='Y'
        result = tesconn.updTESObjAction('update','ServiceJob',tesconn.dict2Xml('OSJob',j),None)
        print(j.fullpath, result.message)
        job_id, jobdata = tesconn.getJob('', re.sub( tesconn.replaceChars(cfg.NEWJOB_EXTENSION) + '$', '', j['fullpath']))
        if job_id != None:
            result = tesconn.updTESObjAction('delete','OSJob',tesconn.dict2Xml('OSJob',jobdata),None)
            print(jobdata.fullpath, result.message)
if sys.argv[1] == valid_options[4]  or sys.argv[1] == '4': #sys.argv[1] == 'check_added_jde_job_deps':
    #get all job dependencies and check if there is a jb that is dependent on a newly created _A job and a none _A equivalently named job(with _A(cfg.NEWJOB_EXTENSION) at the end
    rjobdep = tesconn.getTESList(f"JobDependency","")
    rjobdep[0].sort(key=lambda x: (x.jobid, x.depjobparent,x.depjobname))
    print("Check following jobs for dependency issues")
    for r in rjobdep[0]:
        if r.depjobname.endswith(cfg.NEWJOB_EXTENSION) and r.depjobtype == '8':  # select only _A jobs
            #_t = re.sub( tesconn.replaceChars(cfg.NEWJOB_EXTENSION) + '$', '', r.depjobname)
            # filter where jobid are the ame , dep parent same, ad depjobname = 
            deps = filter(lambda x: x.jobid == r.jobid and  x.depjobparent== r.depjobparent and  x.depjobname ==  re.sub( tesconn.replaceChars(cfg.NEWJOB_EXTENSION) + '$', '', r.depjobname),   rjobdep[0])
            for d in deps:
                __id, __jobdata = tesconn.getJobbyId(d.jobid)
                if __jobdata.type == '8':
                    print(d.jobid, d.jobname, d.depjobname, d.depjobparent)

        #print(r)

