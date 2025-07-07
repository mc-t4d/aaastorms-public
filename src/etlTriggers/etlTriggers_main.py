# t4ds_dev: amorrison@mercycorps.org
# project_partner: Research & Learning, ereid@mercycorps.org
# project_name: AAAStorms
# notes: initial deployment date, 01JUL23

#%%
import botocore
import boto3
from utils import make_soup
import json
import parse_storms as stormy
import io

def handler(event, context):

    '''
    output:
    '''

    print(event)
    try: 
        sesh = boto3.Session(profile_name='aaastorms-dev')
    except Exception as e:
        if type(e) == botocore.exceptions.ProfileNotFound:
            print('profile not found. using default.') 
            sesh = boto3.Session()
    s3 = sesh.client('s3')

    key = [v for k,v in event.items()][0]
    print(f'retrieving storm data from s3://aaastorms-stormdata/{key}')

    obj = s3.get_object(Bucket='aaastorms-stormdata', Key=key)['Body'].read().decode('UTF-8')
    stormevent = json.loads(obj)
    print('evaluating action triggers...')
    print(stormevent)

    storm_data = stormy.get_triggers(stormevent)
    key = f"{storm_data['trigger_type']}/{storm_data['storm_data']['uuid']}_{storm_data['storm_data']['report_date_aaastorms'].replace(' ','_')}_triggers.json"
    response = s3.put_object(
        Body=json.dumps(storm_data),
        Bucket='aaastorms-stormtriggers',   
        Key=key
    )
    
    return {'stormData':storm_data,'key':event}
#%%