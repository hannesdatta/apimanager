# API MANAGER

Manage API data retrieval for research via MongoDB

* WARNING: Package is still under development.

---

## Instructions

### Overview

This module assists researchers in managing data collections from APIs. 
It simplifies the process to the extent that a researcher only has to
specify the API calls to make, with workers handling the 
collection of the required data and storage in a MongoDB. 
At the core of the module is the idea that complex data collections
require a good data infrastructure. To this extent, the module
reports not only on successful API calls, but allows one to also view
back potential error messages and re-collect items that were not collectible.

Each API *request* - i.e., even before any data is retrieved - will be stored in a JSON object.


Attribute                         |               Operationalization
----------------------------------|------------------------------------------------------------------
ts_added | Unix time when request was added
ts_expiry | Expiry time of request (e.g., if it should only be fetched within the next hour; in unix time)
priority | One of high, or low (high-priority requests are fetched first)
url | URL of request
headers	 | Header (not implemented yet) for request
type | Tag to identify type of API call (can be used for querying later on)
endpoint | API endpoint to use; refer to {'module': 'name of python module.py', 'function': 'name of function within module to call'}
jobid | Job ID
retrievals | Array, storing result of each retrieval attempt; with sub-attributes timestamp (timestamp of actual data retrieval in Unixtime), statuscode (HTTP status code of retrieval (200 for ok), and result (actual result of API call, in JSON notation)

Features:
- queue jobs (with unlimited number of API endpoints to call)
- configure own API endpoints, including authentication and retrieval limits
- stores data in MongoDB
- separates data collection from parsing
- automatically splits objects if the object size exceeds MongoDB's limit of 16MBg


### How do I start?

**Configure**

The packages requires a `keys.json` file in the root directory for the configuration.

```
{"mongo": {"connection_string": "mongodb://CONNECTION STRING HERE",
		   "db_name": "api-test"},
"endpoints": ["endpoint_name": {"module": "jsonplaceholder",
								"function": "get",
								"username": "",
								"password": ""}]
}

```

Each `module` needs to be a .py script in the project's root directory; each module's `function` refers to 
a function in `module` that needs to be called when a specific API endpoint needs to be collected.

**Submit jobs**

Testing.py contains example code to submit API requests.

**Start the collection**

To start up the script in worker mode, put `import api_module` in your script,
and call `api_module.run_api()`. The method accepts a filter argument, which can be used
to filter for specific calls. Examples include:



You can also specify a specific filter for which types of API calls to get (such as type strings, or job IDs)

`api_module.run_api({'jobid': '5ddba88b92115a424c88c5a2'})` to retrieve 
data for a specific job, or
`api_module.run_api({'type': 'type-string'})` to filter for a specific type of job.

Use the following snipped as an example startup script for your worker.

```
# Example worker script
import sys
import os
import time
import json

sys.path.append(os.path.dirname(os.path.abspath("apimanager/src/apimanager//api_module.py")))

import api_module
from bson.objectid import ObjectId
  
if (len(sys.argv)>1):
    filter = json.loads(sys.argv[1].replace("'",'"'))
    if 'jobid' in sys.argv[1]: filter['jobid']=ObjectId(filter['jobid'])
else:
    filter = {}
    
while 1==1:
    print('Running with filter: '+str(filter))
    api_module.run_api(filter)
    time.sleep(3)

```

## Setup

### Installation

To install the package locally, run the following in a virtual environment:

    make install

### Updates

To install the latest dependencies, run the following:

    make update

### Tests

To run all tests, run the following:

    make test



### License

apimanager is released under the MIT license:


```

Copyright 2019, Hannes Datta (h.datta@tilburguniversity.edu)

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
