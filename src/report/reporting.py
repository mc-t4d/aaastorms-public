#%%
import json
import boto3
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import botocore

def get_all_s3_keys(bucket, prefix, s3):
    """Get a list of all keys in an S3 bucket."""
    keys = []
    kwargs = {'Bucket':bucket, 'Prefix':prefix}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp['Contents']:
            keys.append(obj['Key'])
        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break
    return keys

def report_text(vars, rep):
    if vars[rep] == None:
        text = 'No report available'
    else:
        text = rep.replace('_',' ')
        text = ' '.join(text.capitalize().split()[:-1]) + ' ' + text.split()[-1].upper()
    return text

def build_reports(trigger):
    env = Environment(loader=FileSystemLoader('templates'))

    if not trigger['trigger_type']:
        template = env.get_template('nomessage.html')
        html = template.render()
    else:
        if trigger['basin'] == 'AL':
            basin = "ATLANTIC"
        elif trigger['basin'] == 'EP':
            basin = "EASTERN PACIFIC"
        else: basin = "ERROR"

        tt = trigger['storm_data']

        template = env.get_template('template.html')
        html = template.render(basin=basin,
                                ttype=trigger['trigger_type'],
                                reason=', '.join(trigger['reason']),
                                report_date_noaa=tt['report_date_noaa'],
                                report_date_adam=tt['report_date_adam'],
                                name=tt['name'],
                                id_noaa=tt['id_noaa'],
                                classification_noaa=tt['classification_noaa'],
                                gdacs_alert_level=tt['gdacs_alert_level_adam'],
                                countries_adam=tt['countries_adam'],
                                subnational_impacts_adam=tt['subnational_impacts_adam'],
                                pop_text=report_text(tt,'subnational_impacts_adam'),
                                watches_noaa=', '.join(tt['watches_noaa']),
                                warnings_noaa=', '.join(tt['warnings_noaa']),
                                max_sustainedwinds_noaa=tt['max_sustainedwinds_noaa'],
                                current_windspeed_noaa=tt['current_windspeed_noaa'],
                                windforecast_noaa=tt['windforecast_noaa']['forecast'],
                                wind_report_adam=tt['wind_report_adam'],
                                wind_text=report_text(tt,'wind_report_adam'),
                                est_stormsurge=tt['est_stormsurge'],
                                max_stormsurge=tt['max_stormsurge_adam'],
                                rainfall_report_adam=tt['rainfall_report_adam'],
                                rain_text=report_text(tt,'rainfall_report_adam'),
                                summary_link_noaa=tt['summary_link_noaa'],
                                report_time=str(pd.Timestamp.now()),
                                uuid=tt['uuid']
                                )

    return html

def send_html_email(contents, tolist):
    try: 
        sesh = boto3.Session(profile_name='aaastorms-dev')
    except Exception as e:
        if type(e) == botocore.exceptions.ProfileNotFound:
            print('profile not found. using default.') 
            sesh = boto3.Session()
    ses_client = sesh.client("ses", region_name="us-east-1")
    
    CHARSET = "UTF-8"
    HTML_EMAIL_CONTENT = contents
    verified = ses_client.list_verified_email_addresses()
    '''
    to_addresses = []
    unverified = []
    for to in tolist: 
        if to in verified['VerifiedEmailAddresses']: to_addresses.append(to)
        else: 
            unverified.append(to)
    if unverified: 
        print(f'There were {len(unverified)} unverified Email addresses found in the to list: {unverified}')
    '''
    response = ses_client.send_email(
        Destination={
            "ToAddresses": tolist,
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": CHARSET,
                    "Data": HTML_EMAIL_CONTENT,
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": "AAASTORMS TRIGGER ALERT",
            },
        },
        Source="dataforimpact+aaastorms@mercycorps.org",
    )

    return response

#%%
