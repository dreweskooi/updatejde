import sys
import time
from collections.abc import Iterable
import tesrest
import logging
#logging.info("Start")
import json
import base64
import shlex
jobcnt = 0
COLUMNS = "id,command,parameters,workingdirectory,fullpath,environmentfile,alias,name,parentname"
del_jdexml='''<jobdef><ube>{ube}</ube><version>{version}</version><title>{title}</title><host>{host}</host><printers/><queue>{queue}</queue><printnow/><delete/><nameonly/>
<pdf>{pdf_y}}</pdf><disabledsoverride/><csv/><jdelog>Y</jdelog><jdedebuglog/><summary>Y</summary><debuglevel>{debuglevel}</debuglevel><pollint>5</pollint><objchck/><osacheckbox>N</osacheckbox>
<osaclass/><folder><var.compound/></folder><tag><var.compound/></tag><parms><parm><columnposition>1</columnposition><column>Business Unit</column><value><var.compound/></value><ovdop/><andor/></parm></parms><opts/></jobdef>
'''
import time
"""
Url: https://gist.github.com/wassname/1393c4a57cfcbf03641dbc31886123b8
"""
import unicodedata
import string

valid_filename_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
char_limit = 255

def clean_filename(filename, whitelist=valid_filename_chars, replace=' '):
    # replace spaces
    for r in replace:
        filename = filename.replace(r,'_')
    
    # keep only valid ascii chars
    cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode()
    
    # keep only whitelisted chars
    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename)>char_limit:
        print("Warning, filename truncated because it was over {}. Filenames may no longer be unique".format(char_limit))
    return cleaned_filename[:char_limit]    

# test
#s='fake_folder/\[]}{}|~`"\':;,/? abcABC 0123 !@#$%^&*()_+ clᐖﯫⅺຶ 讀ϯՋ㉘ ⅮRㇻᎠ⍩ 𝁱C ℿ؛ἂeuឃC ᅕ ᑉﺜͧ bⓝ s⡽Հᛕ\ue063 牢𐐥er ᐛŴ n წş .ھڱ                                 df                                         df                                  dsfsdfgsg!zip'
#print(clean_filename(s)) # 'fake_folder_abcABC_0123_____clxi_28_DR_C_euC___bn_s_er_W_n_s_.zip'
class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""

class Timer:
    def __init__(self):
        self._start_time = None

    def start(self):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError(f"Timer is running. Use .stop() to stop it")

        self._start_time = time.perf_counter()

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError(f"Timer is not running. Use .start() to start it")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        if cfg.DEBUG: Print(f"Elapsed time: {elapsed_time:0.4f} seconds")

def Print(*message):
    msg=''
    if isinstance(message, Iterable):
        for m in message:
            msg += m + ' '
    else:
        msg=message
    print(msg)
    logging.info(msg)

def add_job_deps_events(jobid, new_jobid, fullpath, skipped_jobs):
    rjobdep = tesconn.getTESList(f"JobDependency", f"jobid = {jobid}")
    if len(rjobdep[0]) > 1:
        Print('more than 1')
    if len(rjobdep[0]) > 0:
        for rowjobdep in rjobdep[0]:
            _jobid, _jobdata = tesconn.getJob(f"{rowjobdep['depjobname']}{cfg.NEWJOB_EXTENSION}", rowjobdep['depjobparent'])
            if rowjobdep['depjobparent'] + '\\' + rowjobdep['depjobname'] in skipped_jobs:
                continue
            if _jobid != None:
                rowjobdep['depjobid'] = _jobid
            rowjobdep['jobid'] = new_jobid
            rowjobdep['id'] = None
            rowjobdep['ignoredep'] = 'Y'
            result = tesconn.updTESObjAction('create','JobDependency',tesconn.dict2Xml('JobDependency',rowjobdep),logging)                                        
            logging.info(f"JobDependency 1 created for job: {fullpath} : {result.message}")
    rfiledep = tesconn.getTESList(f"FileDependency", f"jobid = {jobid}")
    if len(rfiledep[0]) > 0:
        for rowfiledep in rfiledep[0]:
            if rowfiledep['inheritedagentname'] !='':
                rowfiledep['inheritagent']='Y'
                rowfiledep['connectionid'] = tesconn.getAgentid(rowfiledep['inheritedagentname'])
            rowfiledep['jobid'] = new_jobid
            rowfiledep['id'] = None
            result = tesconn.updTESObjAction('create','FileDependency',tesconn.dict2Xml('FileDependency',rowfiledep),logging)                                                                                
            logging.info(f'FileDependency created : {result.message} for {fullpath}')
    rvardep = tesconn.getTESList(f"VariableDependency", f"jobid = {jobid}")
    if len(rvardep[0]) > 0:
        for rowvardep in rvardep[0]:
            rowvardep['jobid'] = new_jobid
            rowvardep['id'] = None
            rowvardep['variable_id'] = tesconn.getObjectidByName('Variable',rowvardep['variablename'])
            rowvardep['variableid'] = tesconn.getObjectidByName('Variable',rowvardep['variablename'])
            rowvardep['varownerid'] = tesconn.getRuntimeUser(rowvardep['varownername'])
            rowvardep['operator'] = '1'
            result = tesconn.updTESObjAction('create','VariableDependency',tesconn.dict2Xml('VariableDependency',rowvardep),logging)  
            logging.info(f'VariableDependency created : {result.message}')
    if True:
        rjobdep = tesconn.getTESList(f"JobDependency", f"depjobid = {jobid}")

        if len(rjobdep[0]) > 1:
            print('more than 1')

        if len(rjobdep[0]) > 0:
            for rowjobdep in rjobdep[0]:
                __jobid, __jobdata = tesconn.getJobbyId(rowjobdep['jobid'])
                if __jobdata['parentname'] + '\\' + rowjobdep['jobname'] in skipped_jobs:
                    continue
                __jobid, __jobdata = tesconn.getJob(f"{__jobdata['name']}", rowjobdep['depjobparent'])
                if __jobid != None:
                    rowjobdep['jobid'] = __jobid
                    rowjobdep['depjobid'] = new_jobid
                    rowjobdep['id'] = None
                    rowjobdep['ignoredep'] = 'Y'
                    if __jobid =='0' or new_jobid =='0':
                        pass
                    else:
                        result = tesconn.updTESObjAction('create','JobDependency',tesconn.dict2Xml('JobDependency',rowjobdep),logging)                                        
                        logging.info(f"JobDependency 2 created  for job: {fullpath} : {result.message}")
                else:
                    result = tesconn.updTESObjAction('delete','JobDependency',tesconn.dict2Xml('JobDependency',rowjobdep),logging)                                        
                    logging.info(f"JobDependency 2 deleted  for job: {fullpath} : {result.message}")
    rjobevents = tesconn.getTESList(f"EventJobJoin", f"jobid = {jobid}")
    if len(rjobevents[0]) > 0:
        for rowjobevent in rjobevents[0]:
            rowjobevent['jobid'] = new_jobid
            rowjobevent['id'] = None
            result = tesconn.updTESObjAction('create','EventJobJoin',tesconn.dict2Xml('EventJobJoin',rowjobevent),logging)                                        
            logging.info(f'EventJobJoin created : {result.message}')

def add_jdejob(name,parentname,fullpath,newjob, extendedinfo, ube,version, rtu_id, agent_id,jde_servicemst_id):
    job_id = newjob['id']
    envfile = newjob['environmentfile']
    newjob['id']='0'
    jobid_adapt , jobdata_adapt = tesconn.getJob(name=f'{name}{cfg.NEWJOB_EXTENSION}', parent=parentname)
    if jobid_adapt != None:
        newjob['id'] = jobid_adapt
    newjob['type'] = '8'
    newjob['saveoutputoption'] = 'Y'
    '''
<tes:agenttype>11</tes:agenttype>
<tes:agentostype>12</tes:agentostype>
<tes:agentserviceid>11</tes:agentserviceid>
<tes:ownername>ONETAKEDA\ricet</tes:ownername>
<tes:agentname>JDE-985-ENDPOINT</tes:agentname>
<tes:runtimeusername>BXLTEOPF03</tes:runtimeusername>
<tes:servicename>JDEdwards</tes:servicename>

    '''
    if not newjob['name'].endswith(cfg.NEWJOB_EXTENSION): newjob['name'] = newjob['name'] + cfg.NEWJOB_EXTENSION
    newjob['agenttype'] = '11'
    newjob['agentostype'] = '12'
    newjob['agentserviceid'] = jde_servicemst_id
    newjob['servicename'] = 'JDEdwards'
    newjob['jobmst_mode'] = '0'
    newjob['command'] = f"{ube}:{version}"
    newjob._attrs.pop('parameters',None)
    newjob._attrs.pop('environmentfile',None)
    newjob['serviceid'] = jde_servicemst_id
    newjob['extendedinfo'] = extendedinfo
    newjob['id'] ='0'
    newjob._attrs.pop('alias',None)
    newjob['runuserid'] = rtu_id    #jde_jobdata[0].runuserid
    newjob['agentid']   = agent_id  #jde_jobdata[0].agentid
    newjob['inheritagent'] = 'N'
    newjob['active'] = 'N'
    t = Timer()
    t.start()
    #print(extendedinfo)
    result = tesconn.updTESObjAction("create" if newjob['id']== '0' else "update","ServiceJob",tesconn.dict2Xml('Job',newjob),logging)
    if cfg.DEBUG: logging.info(jobcnt, result.message)
    if 'exception' in result.message:
        logging.error('1', newjob.name, newjob.parent)
        logging.error(result.message)
    else:
        jobid_adapt , jobdata_adapt = tesconn.getJob(name=f'{name}{cfg.NEWJOB_EXTENSION}',parent=parentname)
        cnt = 0
        while jobid_adapt == None and cnt < 10:
            time.sleep(0.5)
            cnt +=1
            jobid_adapt , jobdata_adapt = tesconn.getJob(name=f'{name}{cfg.NEWJOB_EXTENSION}',parent=parentname)
        t.stop()
        if jobid_adapt == None:
            logging.info(f"Add new job, stopped after 10 tries f'{fullpath}{cfg.NEWJOB_EXTENSION}'")
            sys.exit(99)
        else:
            return (job_id, jobid_adapt,jobdata_adapt.fullpath)
            pass
            #add_job_deps_events(job_id, jobid_adapt,jobdata_adapt.fullpath)

def add_jde_jobs():
    Print(f'Start Update Jobs based on selection criteria')
    Print(f"Filter : {cfg.JOBGROUP_SELECT}")
    servicemast = tesconn.getTESList("Service","name='JDEdwards'")
    if len(servicemast[0])==0:
        Print("JDEdwards Service not found")
        sys.exit(12)
    jde_servicemst_id = servicemast[0][0]['id']

    cnt_jde_already_exist =0
    cnt_jde_new =0
    missing_envfiles = set()
    missing_server = set()
    missing_rtu = set()
    added_jobs = set()
    skipped_jobs = set()
    jobrows, res = tesconn.getTESList(f"Job", f"type = 2 and fullpath like '{tesconn.replaceChars(cfg.JOBGROUP_SELECT)}\\\\*'",columns=f"{COLUMNS}")     
    for j in jobrows:
        if j.command in cfg.SC_COMMANDS:
            #envfiles.add(j.environmentfile)
            ube =''
            version=''
            title=''
            queue =''
            pdf_y = 'Y'
            debuglevel='0'
            host=''
            skip = False
            parts = shlex.split(j.parameters)
            for x, y in enumerate(parts):
                if parts[x] == '-r':
                    ube = parts[x+1]
                elif parts[x] == '-v':
                    version = parts[x+1]
                elif parts[x] == '-h':
                    host = parts[x+1]
                elif parts[x] == '-q':
                    queue = parts[x+1]
                elif parts[x] == '-g':
                    debuglevel = parts[x+1]
                elif parts[x].startswith('-r') and len(parts[x])> 2:
                    ube = parts[x][2:]
                elif parts[x].startswith('-v'):
                    version = parts[x][2:]
                else:

                    if parts[x].startswith('-'):
                        Print('ERROR Job : ', j.fullpath, ' ,Unknown option, job will be skipped ', parts[x])
                        skipped_jobs.add(j.fullpath)
                        skip=True
                        continue

            jdexml2=f'''
                      <jobdef><ube>{ube}</ube><version>{version}</version><title>{title}</title><host>{host}</host><printers/><queue>{queue}</queue><printnow/><delete/><nameonly/>
<pdf>Y</pdf><disabledsoverride/><csv/><jdelog/><jdedebuglog/><summary>Y</summary><debuglevel>0</debuglevel><pollint>5</pollint><objchck/><osacheckbox>N</osacheckbox><osaclass/>
<folder><var.compound/></folder><tag><var.compound/></tag></jobdef>
'''
            if skip:
                continue
            # Now get envfile mapping data and validate that:
            j.environmentfile= j.environmentfile.replace(' ','')
            if j.environmentfile in envfile_mapping:
                pass
            else:
                if not j.environmentfile in missing_envfiles:
                    missing_envfiles.add(j.environmentfile)
                Print(f"ERROR Job: {j.fullpath} ,Environment file not found in mapping {cfg.ENVFILE_MAPPING}: {j.environmentfile}")
                skipped_jobs.add(j.fullpath)
                continue
            jobid, jobdata = tesconn.getJob(f"{j.name}",j.parentname)
            if jobid == None:
                Print("Issue, job should have been found!")
            jobid_adapt, jobdata_adapt = tesconn.getJob(f"{j.name}{cfg.NEWJOB_EXTENSION}",j.parentname)
            if jobid_adapt == None:
                if cfg.UPDATE:
                    Print(f"Will add adapter job : {j.fullpath}")
                else:
                    Print(f"Would add adapter job : {j.fullpath}")
                
                if not '\\' in envfile_mapping[j.environmentfile]['user']:
                    rtu_id = tesconn.getRuntimeUser(cfg.RUNTIMEUSER_DEFAULT_DOMAIN + '\\' +  envfile_mapping[j.environmentfile]['user'])    
                else:
                    rtu_id = tesconn.getRuntimeUser(envfile_mapping[j.environmentfile]['user'])
                if rtu_id == -1: 
                    #if not envfile_mapping[j.environmentfile]['user'] in missing_rtu:
                    Print(f"Missing runtime user {envfile_mapping[j.environmentfile]['user']}")
                    missing_rtu.add(envfile_mapping[j.environmentfile]['user'])
                    continue
                queue = envfile_mapping[j.environmentfile]['queue']
                host=''
                host = envfile_mapping[j.environmentfile]['server']
                title='Title'
                #agent_id = tesconn.getAgentid(envfile_mapping[j.environmentfile]['server'])
                agent_id = tesconn.getAgentidByMachine(envfile_mapping[j.environmentfile]['server'],'JDEDWARDS')
                if agent_id == -1: 
                    missing_server.add(envfile_mapping[j.environmentfile]['server'])
                    Print(f"Missing server: {envfile_mapping[j.environmentfile]['server']}")
                    continue
                cnt_jde_new +=1
                if cfg.UPDATE:
                    jdexml=f'''<jobdef><ube>{ube}</ube><version>{version}</version><title>{title}</title><host>{host}</host><printers/><queue>{queue}</queue><printnow/><delete/><nameonly/>
        <pdf>{pdf_y}</pdf><disabledsoverride/><csv/><jdelog>Y</jdelog><jdedebuglog/><summary>Y</summary><debuglevel>{debuglevel}</debuglevel><pollint>5</pollint><objchck/><osacheckbox/>
        <osaclass/><folder><var.compound/></folder><tag><var.compound/></tag><parms/><opts><var.compound/></opts></jobdef>
        '''
                    #print(jdexml)
                    added_jobs.add(add_jdejob(j.name,j.parentname,j.fullpath,jobdata, jdexml,ube=ube,version=version, rtu_id=rtu_id, agent_id=agent_id, jde_servicemst_id=jde_servicemst_id))
            else:
                cnt_jde_already_exist +=1
                if cfg.DEBUG: Print(f"No need to add adapter job   : {j.fullpath}")
            parent_jobid, parentjob = tesconn.getJob('',j.parentName)
            jbackup = tesconn.dict2Xml('Job',jobdata)

    for addedjob in added_jobs:
        add_job_deps_events(*addedjob, skipped_jobs=skipped_jobs)    
    rc = 0                
    Print(f"JDE jobs new : {cnt_jde_new}")
    Print(f"JDE jobs that already existed : {cnt_jde_already_exist}")
    if missing_envfiles:
        rc=1
        Print("List of missing envfiles")
        for e in missing_envfiles:
            Print("\tERROR",e)            
    if missing_rtu:
        rc=2
        Print("List of missing runtime users")
        for e in missing_rtu:
            Print("\tERROR",e)  
    if missing_server:          
        rc=3
        Print("List of missing agents")
        for e in missing_server:
            Print("\tERROR",e)   
    if skipped_jobs:         
        rc=4
        Print("List of skipped jobs because of invalid options ")
        for e in skipped_jobs:
            Print(f"\tERROR",e)            
    return rc

if __name__ == '__main__':     
    try:
        with open('config.json') as f:
            cfg = tesrest.AttrDict(json.load(f))
    except Exception as ex:
        Print("Error in getting CONFIGURATION, check config.json. Exiting")
        sys.exit(11) 
    try:
        with open(cfg.ENVFILE_MAPPING.strip()) as f:
            envfile_mapping = tesrest.AttrDict(json.load(f))
    except Exception as ex:
        Print(f"Error in getting envfile_mapping, check config.json, missing mapping file : {cfg.ENVFILE_MAPPING.strip()}. Exiting")
        sys.exit(11)  
    Print(f"Connecting to {cfg.TIDAL_CM}")
    tesconn = tesrest.TESREST(cfg.TIDAL_CM, cfg.CM_USER,base64.b85decode(cfg.CM_PASSWORD).decode('utf-8'))  
    logfile = f'UPDATEJDE_SC_{clean_filename(cfg.JOBGROUP_SELECT)}.log'
    print("Will use logfile\n\t",logfile)
    #if os.path.exists(logfile):
    #    os.remove(logfile)
    #job_data, jobid = tesconn.getJob('01 Reprice Bulk (SA,TS) at 545 (R42950 PSRF0008)', '\\JDE 9.0\\Refined Fuels\\06:00-19:00 Manual Bulk Processing')    
    #jde_jobdata2, jde_jobid = tesconn.getTESList("Job","fullPath='\\\\10 As Of ledger posting \(R41542  PSAG0008\)'")
    handler = logging.basicConfig(filename=logfile, force=True, encoding='utf-8', level=logging.DEBUG if cfg.DEBUG else logging.INFO )
    if cfg.UPDATE:
        Print("Update mode")
        Print("Will first run non-update validation")
        cfg.UPDATE = False
        rc = add_jde_jobs()
        Print(f"Completed non-update validation processing, rc={rc}")
        if rc == 0 or  ("UPDATE_ON_ISSUES" in cfg and cfg.UPDATE_ON_ISSUES):
            cfg.UPDATE = True
            rc = add_jde_jobs()
            Print(f"Completed update processing, rc={rc}")
        else:
            Print(f"Stopped update processing because of issues found, rc={rc}")
    else:
        Print("Non update mode")
        rc= add_jde_jobs()
        Print(f"Completed non-update processing, rc={rc}")