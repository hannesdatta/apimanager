###########################
# API get's little helper #
#   ~ Management tool ~   #
###########################

import time
import sys
import datetime
import json
import pymongo as pymongo
from bson.objectid import ObjectId
import math
import re
import auth_keys
import bson
import copy

#############################################
  
def startup():
    print('Starting up connection to MongoDB server...')
    global apimanagement_db
    global endpoints
    global keys
        
    maxSevSelDelay = 1000
    keys=auth_keys.load_keys()
    try:
        client = pymongo.MongoClient(keys['mongo']['connection_string'],
                                     serverSelectionTimeoutMS=maxSevSelDelay)
        client.server_info() # force connection on a request as the
                             # connect=True parameter of MongoClient seems
                             # to be useless here 
        print('connected to mongo db server!')
    except pymongo.errors.ServerSelectionTimeoutError as err:
        # do whatever you need
        print(err)
        
    apimanagement_db=client[keys['mongo']['db_name']]

#############################################

def dump_data(jsonobj, fn):
    from bson.json_util import dumps
    f=open(fn,'w', encoding='utf-8')
    for te in jsonobj:
        f.write(dumps(te))
        f.write('\n')
    f.close()
    
# build indices
def api_buildindices():
    
    #apimanagement_db.requests.create_index([("ts_expiry", pymongo.ASCENDING)], background=True)
    #apimanagement_db.requests.create_index([("priority", pymongo.ASCENDING)], background=True)
    #apimanagement_db.requests.create_index([("retrievals.status_code", pymongo.ASCENDING)], background=True)
    # The most important index I think is this compound one for sorting:
    #apimanagement_db.requests.create_index([("ts_expiry", pymongo.ASCENDING),("priority", pymongo.ASCENDING)], background=True)

    if (0==1):
        apimanagement_db.requests.create_index([("priority", pymongo.ASCENDING), 
                                                ("ts_expiry", pymongo.ASCENDING),
                                               ("status", pymongo.ASCENDING),
                                               ("ts_added", pymongo.ASCENDING),
                                               ("retrievals.status_code", pymongo.ASCENDING),
                                               ("retrievals.timestamp", pymongo.ASCENDING)
                                               ])

        apimanagement_db.requests.create_index([("priority", pymongo.ASCENDING), 
                                                ("ts_expiry", pymongo.ASCENDING),
                                               ("status", pymongo.ASCENDING),
                                               ("retrievals.status_code", pymongo.ASCENDING),
                                               ("retrievals.timestamp", pymongo.ASCENDING)
                                               ])
        apimanagement_db.requests.create_index([("ts_expiry", pymongo.ASCENDING),
                                               ("status", pymongo.ASCENDING),
                                               ("retrievals.status_code", pymongo.ASCENDING),
                                               ("priority", pymongo.ASCENDING)
                                               ])
        apimanagement_db.requests.create_index([("ts_expiry", pymongo.ASCENDING),
                                               ("status", pymongo.ASCENDING),
                                               ("retrievals.status_code", pymongo.ASCENDING)
                                               ])

        apimanagement_db.requests.create_index([("type", pymongo.ASCENDING),
                                                ("retrievals.status_code", pymongo.ASCENDING)
                                               ])

        apimanagement_db.requests.create_index([("ts_added", pymongo.ASCENDING)
                                               ])

        apimanagement_db.requests.create_index([("priority", pymongo.ASCENDING),
                                                ("ts_expiry", pymongo.ASCENDING)
                                               ])

        apimanagement_db.requests.create_index([("ts_expiry", pymongo.ASCENDING)
                                               ])

        apimanagement_db.requests.create_index([("retrievals.timestamp", pymongo.ASCENDING)
                                               ])
        apimanagement_db.requests.create_index([("retrievals.status_code", pymongo.ASCENDING)
                                               ])

        apimanagement_db.requests.create_index([("status", pymongo.ASCENDING)
                                               ])
        apimanagement_db.requests.create_index([("priority", pymongo.ASCENDING),
                                                ("ts_expiry", pymongo.ASCENDING)
                                               ])
    
        apimanagement_db.requests.create_index([("jobid", pymongo.ASCENDING)])
    
        #apimanagement_db.requests.index_information()

# post API get requests to DB
def api_request(urls, typestr, endpoint, expiry=4*60*60, priority="low", jobid=ObjectId()):
    tsadded = math.floor(time.time())
    tsexpiry = tsadded+expiry
    dics = []
    if not isinstance(urls, list): urls=[urls]
    
    for url in urls:
        dic = {"ts_added" : tsadded,
               "ts_expiry" : tsexpiry,
               "priority" : priority,
               "url" : url,
               "headers": 'default',
               "type": typestr,
               "endpoint": endpoint,
               "jobid": jobid,
               "retrievals" : []}
        dics.append(dic)
    
    api_buildindices()
    
    ids = apimanagement_db.requests.insert_many(dics)
    return(ids.inserted_ids)

# how to deal with objects larger than 16MB?
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def chunkIt(seq, num):
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg

    return out

def split_obj(x, nchunks,node='obj'):
    chobj=list(chunkIt(x.get(node),nchunks))
    result=[]
    for ch in chobj:
        copyobj=x.copy()
        copyobj[node]=ch
        result.append(copyobj)
    return(result)


def get_function(module, function='get'):
    mod= __import__(module)
    func = getattr(mod, function)
    return(func)

# execute API get request for a specific retrieval request from the DB
def api_retrieve_ids(objectids):
    for o in objectids:
        obj = apimanagement_db.requests.find_one({"_id": o})
        print('getting object')
        try:
            try:
                endpoint=keys.get('endpoints').get(obj['endpoint'])
            except:
                internal_endpoint=bool(re.search('SNS/socialStat', obj['url']))
                if internal_endpoint==True:
                    endpoint = {'module':'chartmetric_website', 'function':'cmsite_get'}
                else:
                    endpoint = {'module':'chartmetric', 'function':'chartmetric_get'}
            
            get=get_function(endpoint['module'], endpoint['function'])
            
            jsonget=get(obj['url'])
                    
            try:
                resp = json.loads(jsonget.text)
            except:
                resp = {'error': jsonget.text}
            if (jsonget.status_code==429): 
                print('Retrieval limt reached; sleeping for 10 seconds')
                time.sleep(10)
            
            mbsize = len(bson.BSON.encode(resp))/1024/1024
            
            if mbsize>14:
                required_splits = math.ceil((mbsize/16)*1.50)
                splitted_obj=split_obj(resp, required_splits)
            else:
                splitted_obj = [resp]

            retrieval = []
            
            for retr in splitted_obj:
                retrieval.append({'timestamp' : math.floor(time.time()),
                                  'status_code': jsonget.status_code,
                                   'response' : retr
                                         })

        except:
            resp = {'error': "Unexpected error:"+ str(sys.exc_info()[0])}
            retrieval = [{'timestamp' : math.floor(time.time()),
                         'status_code': 9990,
                         'response' : resp
                         }]
            time.sleep(1)
                   
        if (retrieval[0]['status_code']!=200):
            print('Timestamp:',datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
            print(retrieval)
        
        
        cnt=0
        insert_obj = []

        for retr in retrieval:
            obj_insert = copy.deepcopy(obj)
            obj_insert['retrievals'].append(retr)
            if (cnt>0): 
                obj_insert['orig_id'] = o
                del obj_insert['_id']
            insert_obj.append(obj_insert)
            cnt+=1

        #obj['retrievals'].append(retrieval)
        
        print('updating')
        # insert objects into Mongo
        cnt=0
        for ins in insert_obj:
            cnt+=1
            if (cnt==1): 
                apimanagement_db.requests.update_one({'_id':o}, {"$set": ins}, upsert=False)
                print(o)
            if (cnt>1): 
                insid=apimanagement_db.requests.insert_one(ins)
                print(insid.inserted_id)
        #apimanagement_db.requests.update_one({'_id':o}, {"$set": obj}, upsert=False)
        print('done updating')

# find IDs of retrieval requests that are still open
def get_queue(currtime=math.floor(time.time()), graceperiod=0, limit = 10, filter = {}):
    # find downloadable objects; ignore the ones with more than 3 attempts ($size).
    # first sort by priority, then by expiry timestamps (first in, last out)
    
    pipeline = {"ts_expiry": { '$gte': currtime-graceperiod},
                "retrievals": {"$exists":"true"}, 
                "$or" : [ {"retrievals": {"$size": 0}},{"retrievals": {"$size": 1}},{"retrievals": {"$size": 2}},
                         {"retrievals": {"$size": 3}},{"retrievals": {"$size": 4}}], 
                "retrievals.status_code": {"$not": {"$eq": 200}}}
    if len(filter)>0: 
        filter.update(pipeline)
    else:
        filter = pipeline
    
    obj = apimanagement_db.requests.find(filter, {'_id':1}).sort([("priority", 1), ("ts_expiry", 1)]).limit(limit)
    
    ids=[]
    for i in obj:
        ids.append(i['_id'])
    
    return(ids)


# wait for API get results, returns JSON object (e.g., used for 
# calls that have dependencies to build subsequent calls (such as 'total', listing
# the total number of items to receive...
def api_getnow(objectid, timeout = 20):
    expire=time.time()+timeout
    
    found = False
    c=0
    while (found==False):
        c=c+1
        obj = apimanagement_db.requests.find_one({"_id": objectid, 'retrievals.status_code':200})
        if obj is not None: 
            found = True
            break
        
        time.sleep(1)
        
        if (time.time()>expire): 
            print('expired!')
            break
    
    tss=[]
    if obj is not None:
        cntr=0
        for o in obj['retrievals']:
            if (o['status_code']==200): tss.append([o['timestamp'], cntr])
            cntr=cntr+1
    tss.sort()

    if (len(tss)>0):
        retobj=obj['retrievals'][tss[0][1]]['response']
        retobj['url'] = obj['url']
        return(retobj)
    else:
        return({})


# retrieve specific fields from successful retrieval requests (status = 200),
# given a specific type (filtered on specific data objects 

# to be depreciated!!!
def api_get_results(type, fields=[], limit=-1, success = False):
    getf = {"url": 1, "retrievals.timestamp":1, "retrievals.status_code" : 1}
    
    if (success==True): 
        pipeline=[{ "$match": { "type": type, "retrievals.status_code": 200}}]
    else:
        pipeline=[{ "$match": { "type": type}}]
        
    pipeline.append(
        { "$project": {"ts_added": 1, "ts_expiry": 1, "priority": 1, "url": 1, "headers": 1, "type": 1,
                       "retrievals": {"$slice": ["$retrievals", -1]}}})
    
    if (len(fields)>0):
        for f in fields:
            getf['retrievals.response.'+f] = 1
        pipeline.append({"$project" : getf})
    
    
    if (limit>0):
        pipeline.append({"$limit": limit})
     
    pipeline.append({"$sort": { "retrievals.timestamp": -1 } })
    #print(pipeline)
    res = list(apimanagement_db.requests.aggregate(pipeline,allowDiskUse = True))

    return(res)



def api_status(graceperiod=0):
    import datetime
    
    currtime=time.time()
    # Total number of to-be-downloaded queries
    nopen = apimanagement_db.requests.count_documents( {"ts_expiry": { '$gte': currtime-graceperiod},
                                                        "status": {'$not' : { '$in': ["terminated", "paused"]}},
                                               "$or" : [ {"retrievals" : { "$size" : 0}},
                                                       {"retrievals" : { "$size" : 1}},
                                                       {"retrievals" : { "$size" : 2}}],
                                               "retrievals.status_code": {'$not' : {"$eq": 200}}})
    
    nexpired_not_downloaded = apimanagement_db.requests.count_documents( {
                                               "status": {'$not' : { '$in': ["terminated", "paused"]}},
                                               "ts_expiry": { '$lt': currtime-graceperiod},
                                               "$or" : [ {"retrievals" : { "$size" : 0}},
                                                       {"retrievals" : { "$size" : 1}},
                                                       {"retrievals" : { "$size" : 2}}],
                                               "retrievals.status_code": {'$not' : {"$eq": 200}}})
    
    npaused_terminated = apimanagement_db.requests.count_documents( {
                                               "status": {'$in' : ["terminated", "paused"]}})
    
    n_downloaded = apimanagement_db.requests.count_documents( {"retrievals.status_code": 200})

    n_last_minute = apimanagement_db.requests.count_documents( {"retrievals.timestamp": {'$gte' : currtime-1*60}})
    n_last_5minutes = apimanagement_db.requests.count_documents( {"retrievals.timestamp": {'$gte' : currtime-5*60}})

    n_errlast_minute = apimanagement_db.requests.count_documents( {"retrievals.timestamp": {'$gte' : currtime-1*60},
                                                               "retrievals.status_code": {'$not' : {"$eq": 200}}})
    n_errlast_5minutes = apimanagement_db.requests.count_documents( {"retrievals.timestamp": {'$gte' : currtime-5*60},
                                                               "retrievals.status_code": {'$not' : {"$eq": 200}}})
    
    printobj = []
    printobj.append(datetime.datetime.fromtimestamp(currtime).strftime('%Y-%m-%d %H:%M:%S'))
    printobj.append('=============================================')
    printobj.append('Grace period: '+str(graceperiod)+ ' seconds')
    printobj.append('')
    printobj.append("Number of API calls in queue: "+str(nopen))
    printobj.append("Expected time (in hrs) for completion: "+ str(datetime.timedelta(hours=(nopen/40)/60)))   
    printobj.append('')
    printobj.append("Number expired API calls: "+str(nexpired_not_downloaded))
    printobj.append("Number paused or terminated API calls: "+str(npaused_terminated))
    
    printobj.append("Number of successful API calls: "+str(n_downloaded))
    printobj.append("Number of API calls in last minute (max. is 50): "+ str(n_last_minute))
    printobj.append("Number of API calls in last 5 minutes (max. is 250): "+ str(n_last_5minutes))
    
    printobj.append("Number of error API calls in last minute: "+str(n_errlast_minute))
    printobj.append("Number of error API calls in last 5 minutes: "+str(n_errlast_5minutes))
    printobj.append('')
    print('\n'.join(printobj))
    return(printobj)
    

####################
## Job management ##
####################

def api_job_add(descr, expiry = 4*60*60, comments = ''):
    tsadded = math.floor(time.time())
    tsexpiry = tsadded+expiry
    ids = []
    dic = {"descr": descr,
           "ts_added" : tsadded,
           "ts_expiry" : tsexpiry,
           "ts_done": 0,
           "comments": comments,
           "ids" : []}
    job = apimanagement_db.jobs.insert_one(dic)
    return(job.inserted_id)

# to be deprecated; job ID will now be inserted directly in requests
def api_job_insertids(jobid, ids):
    obj = apimanagement_db.jobs.find_one({"_id": jobid})

    for id in ids:
        obj['ids'].append(id)

    upd=apimanagement_db.jobs.update_one({'_id':jobid}, {"$set": obj}, upsert=False)
    return(upd)

###########################################################
## Find jobs of most recent 5 scrapes in the last minute ##
###########################################################

def show_current_jobs():
    import datetime

    currtime=time.time()
    lastminute = apimanagement_db.requests.find( {"retrievals.timestamp": {'$gte' : currtime-1*60}}, {"url":1}).limit(5)
    lastminute_ids = []
    lastminute_table = []
    for l in lastminute: 
        lastminute_ids.append(l['_id'])
        lastminute_table.append(l)

    from IPython.display import HTML, display
    import tabulate
    display(HTML(tabulate.tabulate(lastminute_table, tablefmt='html')))

    # find associated job
    res=apimanagement_db.jobs.find( {"ids": {"$in" : lastminute_ids}}, {"_id":1, "ts_added":1, "descr":1, "comments":1})

    job_array = []
    for job in res:
        ts=datetime.utcfromtimestamp(job['ts_added']).strftime('%Y-%m-%d %H:%M')
        comments = ''
        try:
            comments = job['comments']
        except:
            comments=''
        job_array.append([str(job['_id']), job['descr'], ts])

    from IPython.display import HTML, display
    import tabulate
    display(HTML(tabulate.tabulate(job_array, tablefmt='html')))
    
def show_all_jobs():
    ###########################
    # get list of logged jobs #
    ###########################

    from datetime import datetime
    all_jobs=apimanagement_db.jobs.find( {})
    job_array = []
    for job in all_jobs:
        ts=datetime.utcfromtimestamp(job['ts_added']).strftime('%Y-%m-%d %H:%M')
        comments = 'no comment'
        try:
            comments = job['comments']
        except:
            comments='no comment'
        job_array.append([str(job['_id']), job['descr'], comments, ts, len(job['ids'])])

    #from IPython.display import HTML, display
    #import tabulate
    #display(HTML(tabulate.tabulate(job_array, tablefmt='html')))
    [print(*line) for line in job_array]

# Set a job's associated IDs statuses (e.g., paused, terminated, active)
# to be updated!!!
def update_job_status(jobid, new_status):
    #jobids=apimanagement_db.jobs.find_one( {'_id' : jobid}, { "ids" : 1})
    #ids = jobids['ids']

    obj = {}
    obj['status'] = new_status
    if (new_status=='delete'):
        res=apimanagement_db.requests.delete_many({"jobid": jobid})
        cnt=res.deleted_count
        print('Deleted ' + str(cnt)+' documents.')
        res=apimanagement_db.jobs.delete_many({"_id": jobid})
        
    else:
        res=apimanagement_db.requests.update_many({"jobid": jobid}, {"$set": obj}, upsert=False)
        cnt=res.modified_count
        print('Modified ' + str(cnt)+' documents.')
    

def get_job_status(objid):
    #objid='5cdbd03992115a16cc5828c6'
    job = apimanagement_db.jobs.find_one({"_id": ObjectId(objid)})
    
    nosuccessful=apimanagement_db.requests.count_documents({'jobid':objid, 'retrievals.status_code':200})
    noitems=apimanagement_db.requests.count_documents({'jobid':objid})
    
    ret=job
    ret['number_of_items'] = noitems
    ret['number_of_completed_items'] = nosuccessful
    ret['completion_rate'] = nosuccessful/noitems
    return(ret)
    
startup()

#############################################
# Check if script is running in worker mode #
#############################################


# retrieval job
def run_api(filter = {}):
    print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    ids=get_queue(graceperiod=150*24*60*60, limit = 200, filter = filter) # get it in chunks of 10
    print(str(len(ids)), 'API calls to go...')
    if (len(ids)>0): 
        api_retrieve_ids(ids)
    else:
        print('Empty queue; sleeping for 10 minutes...')
        time.sleep(10*60)
        
        
if (len(sys.argv)>1): 
    if sys.argv[1]=='worker':
        if (len(sys.argv)>2):
            filter = json.loads(sys.argv[2].replace("'",'"'))
        else:
            filter = {}
            
        while 1==1:
            print('Running with filter: '+str(filter))
            run_api(filter)
            time.sleep(3)
