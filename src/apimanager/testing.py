# Initialize connection to MongoDB and load packages
import api_module

# Upon first start: Initialize database
api_module.api_buildindices()


################
# Submit a job #
################

# assemble URLs
urls=[]
for i in range(1, 20+1):
    urls.append('https://jsonplaceholder.typicode.com/todos/'+str(i))
    

# add job
jobid=api_module.api_job_add('test-todo', expiry=24*60*60, comments = 'testing for andrea')
print(jobid)

ids=api_module.api_request(urls, typestr='json-todo', endpoint='endpoint_demo', jobid=jobid)
# no need to do anything with these IDs

#############
# View data #
#############

res=api_module.apimanagement_db.requests.find({'jobid':jobid}).limit(10)

for i in res:
    print(i)

# similarly
res=api_module.apimanagement_db.requests.find({'type':'json-todo'}).limit(10)

for i in res:
    print(i)

######################################################################################
# Wait for retrieval by worker; return object if it exists within a specific timeout #
######################################################################################
    
objid=api_module.api_request(urls[0], typestr='json-todo', endpoint='endpoint_demo')

api_module.api_getnow(objid, timeout=30)


################################ 
# View retrieval status of API #
################################

out=api_module.api_status()

##################
# Job management #
##################

# All jobs
api_module.show_all_jobs()

# Specific job
from bson.objectid import ObjectId
api_module.get_job_status(ObjectId('5ddad773efff45157d0c32c3'))

# Delete jobs
api_module.update_job_status(ObjectId('5ddad6f499ba978d158e6c4f'), 'delete')

# Update job status (e.g., to paused)
api_module.update_job_status(ObjectId('5ddad6f499ba978d158e6c4f'), 'paused')


# Delete all requests
# api_module.apimanagement_db.requests.delete_many({})




    
  

# To do: 
# - Make data collection a bit more complex; i.e., get IDs from already collected jobs, then get related data, etc
#   o get list of 100, break at 20; then resume at 21.
# - Revise/optimize indexes
# 
    