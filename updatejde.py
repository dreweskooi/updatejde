from audioop import add
from ctypes.wintypes import PINT
from modulefinder import IMPORT_NAME
import queue
import sys
import time

import tesrest
import logging
logging.info("Start")
import config 
import os
import datetime 
import json
import base64
import shlex
jobcnt = 0

jdexml='''<jobdef><ube>{ube}</ube><version>{version}</version><title>{title}</title><host>{host}</host><printers/><queue>{queue}</queue><printnow/><delete/><nameonly/>
<pdf>{pdf_y}}</pdf><disabledsoverride/><csv/><jdelog>Y</jdelog><jdedebuglog/><summary>Y</summary><debuglevel>{debuglevel}</debuglevel><pollint>5</pollint><objchck/><osacheckbox>N</osacheckbox>
<osaclass/><folder><var.compound/></folder><tag><var.compound/></tag><parms><parm><columnposition>1</columnposition><column>Business Unit</column><value><var.compound/></value><ovdop/><andor/></parm></parms><opts/></jobdef>
'''
import time

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
        print(f"Elapsed time: {elapsed_time:0.4f} seconds")

def Print(*message):
    msg=''
    if type(message) == list:
        for m in message:
            msg += m
    else:
        msg=message
    print(msg)
    logging.info(msg)

def add_job_deps_events(jobid, new_jobid, fullpath):
    rjobdep = tesconn.getTESList(f"JobDependency", f"jobid = {jobid}")
    if len(rjobdep[0]) > 0:
        for rowjobdep in rjobdep[0]:
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
    rjobdep = tesconn.getTESList(f"JobDependency", f"depjobid = {jobid}")
    if len(rjobdep[0]) > 0:
        for rowjobdep in rjobdep[0]:
            rowjobdep['depjobid'] = new_jobid
            rowjobdep['id'] = None
            rowjobdep['ignoredep'] = 'Y'
            result = tesconn.updTESObjAction('create','JobDependency',tesconn.dict2Xml('JobDependency',rowjobdep),logging)                                        
            logging.info(f"JobDependency 2 created  for job: {fullpath} : {result.message}")
    rjobevents = tesconn.getTESList(f"EventJobJoin", f"jobid = {jobid}")
    if len(rjobevents[0]) > 0:
        for rowjobevent in rjobevents[0]:
            rowjobevent['jobid'] = new_jobid
            rowjobevent['id'] = None
            result = tesconn.updTESObjAction('create','EventJobJoin',tesconn.dict2Xml('EventJobJoin',rowjobevent),logging)                                        
            logging.info(f'EventJobJoin created : {result.message}')

def add_jdejob(name,parentname,fullpath,newjob, extendedinfo, ube,version, rtu_id, agent_id):
    job_id = newjob['id']
    envfile = newjob['environmentfile']
    newjob['id']='0'
    jobid_adapt , jobdata_adapt = tesconn.getJob(name=f'{name}_adapt', parent=parentname)
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
    if not newjob['name'].endswith('_adapt'): newjob['name'] = newjob['name'] + "_adapt"
    newjob['agenttype'] = '11'
    newjob['agentostype'] = '12'
    newjob['agentserviceid'] = jde_jobdata[0]['agentserviceid']
    newjob['servicename'] = 'JDEdwards'
    newjob['jobmst_mode'] = '0'
    newjob['command'] = f"{ube}.{version}"
    newjob['serviceid'] = jde_jobdata[0].serviceid
    newjob['extendedinfo'] = extendedinfo
    newjob['id'] ='0'
    newjob._attrs.pop('alias',None)
    newjob['runuserid'] = rtu_id    #jde_jobdata[0].runuserid
    newjob['agentid']   = agent_id  #jde_jobdata[0].agentid
    newjob['inheritagent'] = 'N'
    newjob['active'] = 'N'
    t = Timer()
    t.start()
    result = tesconn.updTESObjAction("create" if newjob['id']== '0' else "update","ServiceJob",tesconn.dict2Xml('Job',newjob),logging)
    if cfg.DEBUG: logging.info(jobcnt, result.message)
    if 'exception' in result.message:
        logging.error('1', newjob.name, newjob.parent)
        logging.error(result.message)
    else:
        jobid_adapt , jobdata_adapt = tesconn.getJob(name=f'{name}_adapt',parent=parentname)
        cnt = 0
        while jobid_adapt == None and cnt < 10:
            time.sleep(0.5)
            cnt +=1
            jobid_adapt , jobdata_adapt = tesconn.getJob(name=f'{name}_adapt',parent=parentname)
        t.stop()
        if jobid_adapt == None:
            logging.info(f"Add new job, stopped after 10 tries f'{fullpath}_adapt'")
            sys.exit(99)
        else:
            add_job_deps_events(job_id, jobid_adapt,jobdata_adapt.fullpath)

def add_jde_jobs():
    Print(f'Start Update Jobs based on selection criteria')
    Print(f"Filter : {cfg.LISTSELECT}")
    cnt_jde_already_exist =0
    missing_envfiles = set()
    missing_server = set()
    missing_rtu = set()
    jobrows, res = tesconn.getTESList(f"Job", f"{cfg.LISTSELECT}",columns=f"{cfg.COLUMNS}")     
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
                else:

                    if parts[x].startswith('-'):
                        Print('Job : ', j.fullpath, ' ,Unknow option ', parts[x])
            

            jdexml2=f'''
                      <jobdef><ube>{ube}</ube><version>{version}</version><title>{title}</title><host>{host}</host><printers/><queue>{queue}</queue><printnow/><delete/><nameonly/>
<pdf>Y</pdf><disabledsoverride/><csv/><jdelog/><jdedebuglog/><summary>Y</summary><debuglevel>0</debuglevel><pollint>5</pollint><objchck/><osacheckbox>N</osacheckbox><osaclass/>
<folder><var.compound/></folder><tag><var.compound/></tag></jobdef>
'''

            # Now get envfile mapping data and validate that:
            j.environmentfile= j.environmentfile.replace(' ','')
            if j.environmentfile in envfile_mapping:
                pass
            else:
                if not j.environmentfile in missing_envfiles:
                    missing_envfiles.add(j.environmentfile)
                    Print(f"Job: {j.fullpath} ,Environment file not found in mapping: {j.environmentfile}")
                continue
            jobid, jobdata = tesconn.getJob(f"{j.name}",j.parentname)
            if jobid == None:
                print("Issue, job should have been found!")
            jobid_adapt, jobdata_adapt = tesconn.getJob(f"{j.name}_adapt",j.parentname)
            if jobid_adapt == None:
                Print(f"Will add adapter job : {j.fullpath}")
                
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
                #server = envfile_mapping[j.environmentfile]['server']
                host=''
                title=''
                #agent_id = tesconn.getAgentid(envfile_mapping[j.environmentfile]['server'])
                agent_id = tesconn.getAgentidByMachine(envfile_mapping[j.environmentfile]['server'],'JDEDWARDS')
                if agent_id == -1: 
                    missing_server.add(envfile_mapping[j.environmentfile]['server'])
                    Print(f"Missing server: {envfile_mapping[j.environmentfile]['server']}")
                    continue
                if cfg.UPDATE:
                    jdexml=f'''<jobdef><ube>{ube}</ube><version>{version}</version><title>{title}</title><host>{host}</host><printers/><queue>{queue}</queue><printnow/><delete/><nameonly/>
        <pdf>{pdf_y}</pdf><disabledsoverride/><csv/><jdelog>Y</jdelog><jdedebuglog/><summary>Y</summary><debuglevel>{debuglevel}</debuglevel><pollint>5</pollint><objchck/><osacheckbox>N</osacheckbox>
        <osaclass/><folder><var.compound/></folder><tag><var.compound/></tag><opts/></jobdef>
        '''
                    add_jdejob(j.name,j.parentname,j.fullpath,jobdata, jdexml,ube=ube,version=version, rtu_id=rtu_id, agent_id=agent_id)
            else:
                cnt_jde_already_exist +=1
                if cfg.DEBUG: Print(f"No need to add adapter job   : {j.fullpath}")
            parent_jobid, parentjob = tesconn.getJob('',j.parentName)
            jbackup = tesconn.dict2Xml('Job',jobdata)
    Print(f"JDE jobs already exist : {cnt_jde_already_exist}")
    Print("List of missing envfiles")
    for e in missing_envfiles:
        Print(e)            
    Print("List of missing runtime users")
    for e in missing_rtu:
        Print(e)            
    Print("List of missing agents")
    for e in missing_server:
        Print(e)            
    sys.exit(0) 
    '''
    if not cfg.UPDATEJOBS_XLSX_PREVIEW and jobdata['type'] == '8':
        if serviceName == 'Informatica':
            iics_jobid, iicsjobdata = tesconn.getJob(f"{jobdata['name']}_iics", jobdata['parentname'])
            if iics_jobid == None:
                jobdata['name'] = f"{jobdata['name']}_iics"
                jobdata['type'] = '2'
                if new_command == '':
                    logging.error(f"Error, new job command empty, job :{fullPath}")
                    #jobdata['command'] = 'hostname'
                else:
                    jobdata['command'] = new_command
                jobdata['parameters'] = new_parameters
                agentlistid = tesconn.getObjectidByName('AgentList',new_agentlistname)
                jobdata['agentlistid'] = agentlistid
                jobdata['agentid'] = '0'
                jobdata['agenttype'] = '6'
                jobdata['inheritagent'] = 'N'
                jobdata._attrs.pop('id',None)
                jobdata._attrs.pop('serviceid',None)
                jobdata._attrs.pop('agentid',None)
                jobdata._attrs.pop('servicename',None)
                jobdata._attrs.pop('extendedinfo',None)
                jobdata['unixprofile'] ='0'
                jobdata['runuserid'] = runtimeuserid
                jobdata['usepasswordwinjob'] = 'SC'
                jobdata['usePasswordWinJob'] = 'SC'
                jobdata['alias'] = None
                result = tesconn.updTESObjAction('create','OSJob',tesconn.dict2Xml('OSJob',jobdata),logging)
                logging.info(result.message)
                if 'exception' in result.message:
                    logging.info(f'Will skip processing this row because of error! {fullPath} ')
                    #sys.exit(99)
                time.sleep(1)
                iics_jobid, iicsjobdata = tesconn.getJob(f"{jobdata['name']}", jobdata['parentname'])
                cnt = 0
                while iics_jobid == None and cnt < 10:
                    time.sleep(0.5)
                    cnt +=1
                    iics_jobid, iicsjobdata = tesconn.getJob(f"{jobdata['name']}", jobdata['parentname'])
                if iics_jobid == None:
                    logging.info(f"Stopped after 10 tries {jobdata['name']},  {jobdata['parentname']}")
                    continue
                    s#ys.exit(99)
                jobid, jobdata = tesconn.getJob('',fullPath,cached=False)
                rjobdep = tesconn.getTESList(f"JobDependency", f"jobid = {jobid}")
                if len(rjobdep[0]) > 0:
                    for rowjobdep in rjobdep[0]:
                        rowjobdep['jobid'] = iicsjobdata['id']
                        rowjobdep['id'] = None
                        result = tesconn.updTESObjAction('create','JobDependency',tesconn.dict2Xml('JobDependency',rowjobdep),logging)                                        
                        logging.info(f"JobDependency 1 created for job: {jobdata['name']},  {jobdata['parentname']} : {result.message}")
                rfiledep = tesconn.getTESList(f"FileDependency", f"jobid = {jobid}")
                if len(rfiledep[0]) > 0:
                    for rowfiledep in rfiledep[0]:
                        rowfiledep['jobid'] = iicsjobdata['id']
                        rowfiledep['id'] = None
                        result = tesconn.updTESObjAction('create','FileDependency',tesconn.dict2Xml('FileDependency',rowfiledep),logging)                                                                                
                        logging.info(f'FileDependency created : {result.message}')
                rvardep = tesconn.getTESList(f"VariableDependency", f"jobid = {jobid}")
                if len(rvardep[0]) > 0:
                    for rowvardep in rvardep[0]:
                        rowvardep['jobid'] = iicsjobdata['id']
                        rowvardep['id'] = None
                        rowvardep['variable_id'] = tesconn.getObjectidByName('Variable',rowvardep['variablename'])
                        rowvardep['variableid'] = tesconn.getObjectidByName('Variable',rowvardep['variablename'])
                        rowvardep['varownerid'] = getRuntimeuser(rowvardep['varownername'])
                        rowvardep['operator'] = '1'
                        result = tesconn.updTESObjAction('create','VariableDependency',tesconn.dict2Xml('VariableDependency',rowvardep),logging)  
                        logging.info(f'VariableDependency created : {result.message}')
                rjobdep = tesconn.getTESList(f"JobDependency", f"depjobid = {jobid}")
                if len(rjobdep[0]) > 0:
                    for rowjobdep in rjobdep[0]:
                        rowjobdep['depjobid'] = iicsjobdata['id']
                        rowjobdep['id'] = None
                        result = tesconn.updTESObjAction('create','JobDependency',tesconn.dict2Xml('JobDependency',rowjobdep),logging)                                        
                        logging.info(f"JobDependency 2 created  for job: {jobdata['name']},  {jobdata['parentname']} : {result.message}")
                rjobevents = tesconn.getTESList(f"EventJobJoin", f"jobid = {jobid}")
                if len(rjobevents[0]) > 0:
                    for rowjobevent in rjobevents[0]:
                        rowjobevent['jobid'] = iicsjobdata['id']
                        rowjobevent['id'] = None
                        result = tesconn.updTESObjAction('create','EventJobJoin',tesconn.dict2Xml('EventJobJoin',rowjobevent),logging)                                        
                        logging.info(f'EventJobJoin created : {result.message}')
                jobid, jobdata = tesconn.getJob('',fullPath,cached=False)
                if jobid != None:
                    if cfg.UPDATEJOB_TO_IICS_DELETE_ORIG:
                        result = tesconn.updTESObjAction('delete',jobdata.TESObject,tesconn.dict2Xml(jobdata.TESObject,jobdata),logging)
                        logging.info(f'Delete of {jobdata.name}, result {result.message} ')
                        time.sleep(1)
                        iicsjobid, iicsjobdata = tesconn.getJob('',f'{fullPath}_iics')
                        iicsjobdata['name'] = iicsjobdata['name'].removesuffix('_iics')
                        result = tesconn.updTESObjAction('update',iicsjobdata.TESObject,tesconn.dict2Xml(iicsjobdata.TESObject,iicsjobdata),logging)
                        logging.info(f'Update of {iicsjobdata.name} to original name , result {result.message} ')                                        
                    else:
                        jobdata['name'] = f"{jobdata.name}_iics_del"
                        result = tesconn.updTESObjAction('update',jobdata.TESObject,tesconn.dict2Xml(jobdata.TESObject,jobdata),logging)
                        logging.info(f'Rename to {jobdata.name}, result {result.message} ')
            else:
                logging.info(f"IICS job already created : {iicsjobdata['fullpath']} {iicsjobdata['id']}")                                        
            iicsjobs +=1


    if False:
        runtimeuserid = getRuntimeuser(cfg.IICS_RUNTIME_USER)
        agentlistid = tesconn.getObjectidByName('AgentList',cfg.IICS_AGENT_LIST)
        jobs = tesconn.getTESList('Job',f"fullpath like '{cfg.UPDATEJOB_TO_IICS_FILTER}' and type = '8'")[0]
        for i in range(2, m_row + 1):
            pwc_wf = sheet.cell(row = i, column = colnames.index('powercenter_workflow_name')).value.strip() if sheet.cell(row = i, column = colnames.index('powercenter_workflow_name')).value != None else ''
            tidal_command = sheet.cell(row = i, column = colnames.index('tidal commands')).value.strip() if sheet.cell(row = i, column = colnames.index('tidal commands')).value != None else ''
            for job in jobs:
                if not job.command.startswith(f"{pwc_wf}@") or job.name.endswith('_del_iics'):
                    continue
                jobid, jobdata = tesconn.getJob('',job.fullpath,cached=False)
                if jobid != None:
                    iics_jobid, iicsjobdata = tesconn.getJob(f"{jobdata['name']}_iics", jobdata['parentname'])
                    if iics_jobid == None:
                        jobdata['name'] = f"{jobdata['name']}_iics"
                        jobdata['type'] = '2'
                        jobdata['command'] = cfg.IICS_COMMAND
                        jobdata['parameters'] = tidal_command
                        jobdata['agentlistid'] = agentlistid
                        jobdata['agentid'] = '0'
                        jobdata['agenttype'] = '6'
                        jobdata['inheritagent'] = 'N'
                        jobdata._attrs.pop('id',None)
                        jobdata._attrs.pop('serviceid',None)
                        jobdata._attrs.pop('agentid',None)
                        jobdata._attrs.pop('servicename',None)
                        jobdata._attrs.pop('extendedinfo',None)
                        jobdata['unixprofile'] ='0'
                        jobdata['runuserid'] = runtimeuserid
                        jobdata['usepasswordwinjob'] = 'SC'
                        jobdata['usePasswordWinJob'] = 'SC'
                        jobdata['alias'] = None
                        result = tesconn.updTESObjAction('create','OSJob',tesconn.dict2Xml('OSJob',jobdata),logging)
                        logging.info(result.message)
                        if 'exception' in result.message:
                            logging.info('Will stop processing because of error!')
                            sys.exit(99)
                        time.sleep(1)
                        iics_jobid, iicsjobdata = tesconn.getJob(f"{jobdata['name']}", jobdata['parentname'])
                        cnt = 0
                        while iics_jobid == None and cnt < 10:
                            time.sleep(0.5)
                            cnt +=1
                            iics_jobid, iicsjobdata = tesconn.getJob(f"{jobdata['name']}", jobdata['parentname'])
                        if iics_jobid == None:
                            logging.info(f"Stopped after 10 tries {jobdata['name']},  {jobdata['parentname']}")
                            sys.exit(99)
                        jobid, jobdata = tesconn.getJob('',job.fullpath)
                        rjobdep = tesconn.getTESList(f"JobDependency", f"jobid = {jobid}")
                        if len(rjobdep[0]) > 0:
                            for rowjobdep in rjobdep[0]:
                                rowjobdep['jobid'] = iicsjobdata['id']
                                rowjobdep['id'] = None
                                result = tesconn.updTESObjAction('create','JobDependency',tesconn.dict2Xml('JobDependency',rowjobdep),logging)                                        
                                logging.info(f"JobDependency 1 created for job: {jobdata['name']},  {jobdata['parentname']} : {result.message}")
                        rfiledep = tesconn.getTESList(f"FileDependency", f"jobid = {jobid}")
                        if len(rfiledep[0]) > 0:
                            for rowfiledep in rfiledep[0]:
                                rowfiledep['jobid'] = iicsjobdata['id']
                                rowfiledep['id'] = None
                                result = tesconn.updTESObjAction('create','FileDependency',tesconn.dict2Xml('FileDependency',rowfiledep),logging)                                                                                
                                logging.info(f'FileDependency created : {result.message}')
                        rvardep = tesconn.getTESList(f"VariableDependency", f"jobid = {jobid}")
                        if len(rvardep[0]) > 0:
                            for rowvardep in rvardep[0]:
                                rowvardep['jobid'] = iicsjobdata['id']
                                rowvardep['id'] = None
                                rowvardep['variable_id'] = tesconn.getObjectidByName('Variable',rowvardep['variablename'])
                                rowvardep['variableid'] = tesconn.getObjectidByName('Variable',rowvardep['variablename'])
                                rowvardep['varownerid'] = getRuntimeuser(rowvardep['varownername'])
                                rowvardep['operator'] = '1'
                                result = tesconn.updTESObjAction('create','VariableDependency',tesconn.dict2Xml('VariableDependency',rowvardep),logging)  
                                logging.info(f'VariableDependency created : {result.message}')
                        rjobdep = tesconn.getTESList(f"JobDependency", f"depjobid = {jobid}")
                        if len(rjobdep[0]) > 0:
                            for rowjobdep in rjobdep[0]:
                                rowjobdep['depjobid'] = iicsjobdata['id']
                                rowjobdep['id'] = None
                                result = tesconn.updTESObjAction('create','JobDependency',tesconn.dict2Xml('JobDependency',rowjobdep),logging)                                        
                                logging.info(f"JobDependency 2 created  for job: {jobdata['name']},  {jobdata['parentname']} : {result.message}")
                        rjobevents = tesconn.getTESList(f"EventJobJoin", f"jobid = {jobid}")
                        if len(rjobevents[0]) > 0:
                            for rowjobevent in rjobevents[0]:
                                rowjobevent['jobid'] = iicsjobdata['id']
                                rowjobevent['id'] = None
                                result = tesconn.updTESObjAction('create','EventJobJoin',tesconn.dict2Xml('EventJobJoin',rowjobevent),logging)                                        
                                logging.info(f'EventJobJoin created : {result.message}')
                        jobid, jobdata = tesconn.getJob('',job.fullpath)
                        if jobid != None:
                            if cfg.UPDATEJOB_TO_IICS_DELETE_ORIG:
                                result = tesconn.updTESObjAction('delete',jobdata.TESObject,tesconn.dict2Xml(jobdata.TESObject,jobdata),logging)
                                logging.info(f'Delete of {jobdata.name}, result {result.message} ')
                                time.sleep(1)
                                iicsjobid, iicsjobdata = tesconn.getJob('',f'{job.fullpath}_iics')
                                iicsjobdata['name'] = iicsjobdata['name'].removesuffix('_iics')
                                result = tesconn.updTESObjAction('update',iicsjobdata.TESObject,tesconn.dict2Xml(iicsjobdata.TESObject,iicsjobdata),logging)
                                logging.info(f'Update of {iicsjobdata.name} to original name , result {result.message} ')                                        
                            else:
                                jobdata['name'] = f"{jobdata.name}_iics_del"
                                result = tesconn.updTESObjAction('update',jobdata.TESObject,tesconn.dict2Xml(jobdata.TESObject,jobdata),logging)
                                logging.info(f'Rename to {jobdata.name}, result {result.message} ')
                    else:
                        logging.info(f"IICS job already created : {iicsjobdata['fullpath']} {iicsjobdata['id']}")                                        
                    iicsjobs +=1
        session.commit()            
        logging.info(f'Completed Update Jobs based on Excel input, total jobs : {jobcnt} {filename} ')
    '''                   
#cfg = config.Config()
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

tesconn = tesrest.TESREST(cfg.TIDAL_CM, cfg.CM_USER,base64.b85decode(cfg.CM_PASSWORD).decode('utf-8'))  
logfile = 'UPDATEJDE_SC.log'
if os.path.exists(logfile):
    #handler.doRollover()
    os.remove(logfile)
#job_data, jobid = tesconn.getJob('01 Reprice Bulk (SA,TS) at 545 (R42950 PSRF0008)', '\\JDE 9.0\\Refined Fuels\\06:00-19:00 Manual Bulk Processing')    
#job_data, jobid = tesconn.getJob('8 Adjust Tariff OrderVol LT type(R594111 PSRF0002)', '\\Copy of JDE 9.0\\Refined Fuels\\06:00-19:00 Manual Bulk Processing\\17 Actualize TO LT&TA Reversal')
#jde_jobdata, jde_jobid = tesconn.getTESList("ServiceJob","alias='JDE_TEMPLATE'")
#jde_jobdata2, jde_jobid = tesconn.getTESList("Job","fullPath='\\\\10 As Of ledger posting \(R41542  PSAG0008\)'")
#jde_jobdata2, jde_jobid = tesconn.getTESList("Job","fullPath='\\\\10 As Of ledger posting \(R41542  PSAG0008\)'")
handler = logging.basicConfig(filename=logfile, force=True, encoding='utf-8', level=logging.DEBUG if cfg.DEBUG else logging.INFO )
if cfg.UPDATE:
    Print("Update mode")
else:
    Print("Non update mode")
add_jde_jobs()