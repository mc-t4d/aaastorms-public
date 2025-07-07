# t4ds_dev: amorrison@mercycorps.org
# project_partner: Research & Learning, ereid@mercycorps.org
# project_name: AAAStorms
# notes: initial deployment date, 01JUL23
#%%
import pandas as pd
import datetime as dt
import boto3
import io
import json
import botocore

def logstorms(data, devprofile='aaastorms-dev'):
    '''
    a function to create and store storm logs in s3
    this function is not currently in use
    '''
    
    try: 
        sesh = boto3.Session(profile_name=devprofile)
    except Exception as e:
        if type(e) == botocore.exceptions.ProfileNotFound:
            print('profile not found. using default.') 
            sesh = boto3.Session()

    s3 = sesh.client('s3')
    obj = s3.get_object(Bucket='aaastorms-stormlogs', Key='log.json')['Body'].read()
    stormlog = pd.DataFrame(json.loads(obj))

    if not data['data']: 
        print('No data collected.')
    else:
        for s in data['triggers']['data']:
            if (s['storm_data']['id_noaa'] not in list(stormlog.id_noaa))&(s['trigger_type']=='pretrigger'):
                s['initial_report'] = 'pretrigger'
            elif (s['storm_data']['id_noaa'] not in list(stormlog.id_noaa))&(s['trigger_type']=='trigger'):
                s['initial_report'] = 'trigger'
            else: 
                s['initial_report'] = False

            stormlog.loc[len(stormlog)] = [data['report_time'],
                                        data['uuid'],
                                            s['storm_data']['id_noaa'],
                                            s['storm_data']['report_date_noaa'],
                                            s['storm_data']['classification_noaa'],
                                            s['trigger_type'],
                                            s['reason'],
                                            s['initial_report']
                                            ]
            
    return stormlog

def clearlogs():

    try: 
        sesh = boto3.Session(profile_name='aaastorms-dev')
    except Exception as e:
        if type(e) == botocore.exceptions.ProfileNotFound:
            print('profile not found. using default.') 
            sesh = boto3.Session()
    s3 = sesh.client('s3')
    
    stormlog = pd.DataFrame(columns=['report_time','report_uuid','id_noaa','report_date_noaa','classification_noaa','trigger_type','reason','initial_trigger','alert_sent'])
    no_event = [None] * 8
    stormlog.loc[0] = no_event

    return stormlog


    
#%%
