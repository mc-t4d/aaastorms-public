# t4ds_dev: amorrison@mercycorps.org
# project_partner: Research & Learning, ereid@mercycorps.org
# project_name: AAAStorms
# notes: initial deployment date, 01JUL23
#%%
import os
import parse_storms as stormy
import json
import boto3
from datetime import datetime
from uuid import uuid4
import io
import botocore

def handler(event, context):
    print(event)
    
    rss_urls = ["https://www.nhc.noaa.gov/gis-at.xml",
            "https://www.nhc.noaa.gov/gis-ep.xml"]
    '''
    #These are test urls to use when there are no active storms.
    rss_urls = [
            "https://www.nhc.noaa.gov/rss_examples/gis-at-20130605.xml",
        "https://www.nhc.noaa.gov/rss_examples/gis-ep-20130530.xml"]
    #A test storm can also be found in the config.py file of the report function.
    '''
    print('retrieving storm data...')
    try:
        res = stormy.consolidate_data(rss_urls)
        print('storm data retrieved.')
    except Exception as e:
        print(e)
        raise e

    uuid = uuid4().hex
    if not res['storms']:
        print('no storms found.')
        keys = None
    else: 
        try: 
            sesh = boto3.Session(profile_name='aaastorms-dev')
        except Exception as e:
            if type(e) == botocore.exceptions.ProfileNotFound:
                print('profile not found. using default.') 
                sesh = boto3.Session()
        s3 = sesh.client('s3')
        now = str(datetime.now().isoformat()).split('.')[0]
        keys = []
        for storm in res['storms']:
            data = {    
                'uuid': uuid,        
                'report_time': now,
                'storm': {'data': storm}
            }
            print(f'writing to data for {storm["nhc_atcf"]} to s3...')
            key = f"{data['storm']['data']['storm_uuid']}_{data['report_time'].replace(' ','_').replace(':','_')}.json"
            keys.append({data['storm']['data']['storm_uuid']:key})
            response = s3.put_object(
                    Body=json.dumps(data),
                    Bucket='aaastorms-stormdata',
                    Key=key
                )
        
            print(response)

    return keys
# %%
