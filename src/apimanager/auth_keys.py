import json

def load_keys():
    print('loading authentication credentials')
    try:
        keys = json.loads(open('keys.json').read())
        return(keys)
        #pprint.pprint(keys)
    except:
        print('Login credentials not found.')
        raise

def get_endpoint(endpoint):
    keys=load_keys()
    for i in keys['endpoints']:
        if i['module']==endpoint: return(i)
    return({})