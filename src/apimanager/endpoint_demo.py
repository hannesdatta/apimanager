##########################################
# ENDPOINT CONNECTOR                     #
#                                        #
# JSON Placeholder API (demo)            #
# https://jsonplaceholder.typicode.com   #
#                                        #
# Note: without authentication           #
##########################################

# Chartmetric scripts
from ratelimit import limits, sleep_and_retry
import requests
import auth_keys

keys=auth_keys.load_keys()
  
@sleep_and_retry
@limits(calls=40, period=60)
def get(url):
    r = requests.get(url, timeout=200)
    return(r)
