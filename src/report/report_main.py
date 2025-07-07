#%%
import reporting
import boto3
import botocore
import config
import json
import io

#%%
def handler(event, context):
    '''
    this function checks the pretrigger bucket to determine if this storm 
    report has already been sent. If the report has not been sent, the function builds
    the report and sends it to the distribution list. 
    '''
    try: 
        sesh = boto3.Session(profile_name='aaastorms-dev')
    except Exception as e:
        if type(e) == botocore.exceptions.ProfileNotFound:
            print('profile not found. using default.') 
            sesh = boto3.Session()
    s3 = sesh.client('s3')
    if event['stormData']['trigger_type'] == 'pretrigger':
        keys = reporting.get_all_s3_keys('aaastorms-stormreports', 'pretrigger', s3)
        storm_id = event['stormData']['storm_data']['id_noaa']
        true_keys = 0
        for k in keys:
            if storm_id in k:
                true_keys += 1
        if true_keys == 0: 
            report = True
        else:
            report = False
    elif event['stormData']['trigger_type'] == 'trigger':
        report = True
    else: 
        print('unknown trigger type; please refer to the NOAA website for details on this storm.')
        report = False
    if report == True:
        html = reporting.build_reports(event['stormData'])
        response = reporting.send_html_email(html,
                                    config.tolist
                                    )
        print(response)
        response = s3.put_object(Body=html, Bucket='aaastorms-stormreports', Key=f"{event['stormData']['trigger_type']}/{event['stormData']['storm_data']['uuid']}_{event['stormData']['storm_data']['report_date_aaastorms'].replace(' ','_').replace(':','_')}_report.html")
        print(response)

    else: 
        print('no report generated.')
