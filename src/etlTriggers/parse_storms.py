# t4ds_dev: amorrison@mercycorps.org
# project_partner: Research & Learning, ereid@mercycorps.org
# project_name: AAAStorms
# notes: initial deployment date, 01JUL23
#%%
import feedparser
import geopandas as gpd
import pandas as pd
import requests
from utils import make_soup, unzip_shapefile
from shapely import Point, Polygon
from uuid import uuid4

def noaa_rssfeed(main_rss):
    '''
    a function that parses the noaa rss feed
    args:
    main_rss : the main url to the rss feed
    '''
    feed = feedparser.parse(main_rss)
    if feed['bozo'] == False:
        print('RSS feed was properly formed and retrieved; bozo=False')
    else: 
        print('RSS feed was not properly formed; bozo=True')
        feed = None
    return feed

def get_two():
    '''
    a function to retrieve the tropical weather outlook
    '''
    two_link = 'https://www.nhc.noaa.gov/xgtwo/gtwo_shapefiles.zip'
    gdf = gpd.read_file(two_link, index_parts=True).explode('geometry').reset_index()
    gdf['geometry'] = str(gdf['geometry'])
    for col in gdf.columns:
        if "PROB" in col:
            gdf[col] = [x.replace('%','') for x in gdf[col]]
            gdf[col] = gdf[col].astype(int)

    return gdf.to_dict('records')

def get_cyclones(feed):
    storms = []
    basins = ['AL','EP']
    uuid = uuid4().hex
    for e in feed['entries']:
        if 'There are no tropical cyclones' in e['title']: break
        elif 'Summary' in e['title']:
            keys = [key for key, value in e.items() if 'nhc_' in key.lower()]
            values = [value for key, value in e.items() if 'nhc_' in key.lower()]
            data = dict(zip(keys,values))
            data['source'] = 'noaa'
            if any(b in data['nhc_atcf'] for b in basins):
                storms.append(data)
        else: 
            continue

    for e in feed['entries']:
        for s in storms:
            s['storm_uuid'] = f"{uuid}_{s['nhc_atcf']}"
            if s['nhc_atcf'] in e['title']:
                key = e['title'].split('-')[0].strip().lower().replace(' ','_').replace('/','_')
                s[key] = e['link']
                s[key+'_date'] = e['published']
    return storms

def get_advisories(storms):
    advisory = False
    for s in storms:
        for k in list(s.keys()):
            if ("forecast_[shp]" in k) and ("date" not in k):
                gdf = unzip_shapefile(s[k])
                if gdf.empty:
                    advisory = False
                else: 
                    advisory = len(gdf)
                s['advisories'] = advisory
            else: continue
    return storms

def get_summary_info(storms):
    '''
    a function to parse summary text for storms to get country specific pretriggers and triggers
    args:
    storms : a set of retrieved links from the get_cyclones function in the format {"rss_feed":rss, "links":links}
    '''
    def textsplitter(text1, text2):
        idx1 = text.index(text1)
        idx2 = text.index(text2)
        iterator = iter(text[idx1:idx2].split("\n"))
        return iterator
    
    country_triggers = {}
    countries = [
                 'Mexico',
                 'Jamaica',
                 'Dominican Republic', 
                 'Haiti', 
                 'Belize'
                 'Guatemala',
                 'El Salvador',
                 'Honduras'
                 ]
    for s in storms:
        print(f"retrieving storm summary from: {s['summary']}")
        soup = make_soup(s['summary'])
        text = soup.find_all("div", {"class": "textproduct"})[0].text
        iterator = textsplitter('WATCHES AND WARNINGS','DISCUSSION')
        warnwarn = []
        watchwatch = []
        for t in iterator:
            if ('warning is in effect' in t.lower()) and ('watch' not in t.lower()):
                country = next(iterator)
                while '*' in country:
                    warnwarn.append(country.replace('* ',''))
                    country = next(iterator)
            elif ('watch is in effect' in t.lower()) and ('warning' not in t.lower()):
                country = next(iterator)
                while '*' in country:
                    watchwatch.append(country.replace('* ',''))
                    country = next(iterator)  
        text2 = soup.find_all("div")
        s['country_watches'] = watchwatch
        s['country_warnings'] = warnwarn

        iterator = textsplitter('MAXIMUM SUSTAINED WINDS','PRESENT MOVEMENT')
        for t in iterator: 
            if 'mph'in t.lower():
                s['max_sustained_winds'] = t.split('...')[1].lower()
        
    return storms

def get_wind_forecasts(storms):
    for s in storms:
        for k in list(s.keys()):
            if ("wind_field_[shp]" in k) and ("_date" not in k):
                wind = gpd.read_file(s[k])
                if wind.empty: 
                    s['windforecast_noaa'] = {'status':False,
                                            'time_of_forecast':'',
                                            'forecast':[],
                                        'exception_code':'NO DATA'}
                else:
                    try:
                        forecast = wind[['VALIDTIME','NE','NW','SE','SW']].to_dict('records')
                        s['windforecast_noaa'] = {
                            'status':True,
                            'time_of_forecast': wind['SYNOPTIME'][0],
                            'forecast': forecast
                        }
                    except (KeyError, AttributeError) as e: 
                        s['windforecast_noaa'] = {'status':False,
                                                'time_of_forecast':'',
                                                'forecast':[],
                                            'exception_code':str(e)}
            else: continue
    return storms

def get_adam():
    #ep_box = Polygon([[-140, 30],[-98, 30],[-98, 0],[-140, 0]])
    #al_box = Polygon([[-98, 30],[-50, 30],[-98, 0],[-50, 0]])
    storm_names = []
    all_storms = []
    
    #r = requests.get('https://x8qclqysv7.execute-api.eu-west-1.amazonaws.com/dev/events/cyclones')
    #adam = r.json()['features']
    
    #for f in adam:
    #    storm_data = f['properties']
        #for label, box in [('AL',al_box), ('EP',ep_box)]:
            #intersection = box.contains(Point(storm_data['longitude'],storm_data['latitude']))
            #if intersection == True:
                #storm_data['basin'] = label
    #    adam_name = f['properties']['name'].split('-')[0]
    #    storm_data['source'] = 'adam'
    #    all_storms.append(storm_data)

    return all_storms

def get_subhazards():

    floods = []
    #countries = ['Guatemala','Nicarauga','Honduras','El Salvador','Belize','Mexico']    
    #r = requests.get('https://x8qclqysv7.execute-api.eu-west-1.amazonaws.com/dev/events/floods')
    #floods_data = r.json()['features']
    #for f in floods_data:
    #    flood = f['properties']
    #    if flood['country'] in countries:
    #        floods.append(flood)
    return floods

def get_gdacs():
    feed = noaa_rssfeed('https://www.gdacs.org/xml/rss.xml')
    return feed

def consolidate_data(urls: list):
    storms = []
    for u in urls: 
        print(f'retriving rss feed: {u}')
        feed = noaa_rssfeed(u)
        s = get_cyclones(feed)
        s = get_advisories(s)
        s = get_summary_info(s)
        s = get_wind_forecasts(s)
        storms.extend(s)

    return {
        'tropical_weather_outlook':get_two(),
        'storms':storms
            }

def get_triggers(storm):

    countries = ['Guatemala','Nicarauga','Honduras','El Salvador','Belize','Mexico']    
    reasons = ['storm_presence']
    
    s = storm['storm']['data']
    for c in s['country_watches']:
        if c in countries:
            reasons.append('active_watch')
    for c in s['country_warnings']:
        if c in countries:
            reasons.append('active_warning')       
    soup = make_soup(s['summary'])
    text = soup.find_all("div", {"class": "textproduct"})[0].text
    basin = s['nhc_atcf'][:2]
    if 'active' in reasons:
        trigger_type = 'trigger'
    else: trigger_type = 'pretrigger'
    storm_data = {
        'trigger_type':trigger_type,
        'reason':reasons,
        'basin':basin,
        'storm_data': {
            'uuid':s['storm_uuid'],
            'name':s['nhc_name'],
            'id_noaa':s['nhc_atcf'],
            'classification_noaa':s['nhc_type'],
            'max_category': None,
            'current_windspeed_noaa':s['nhc_wind'],
            'max_sustainedwinds_noaa':s['max_sustained_winds'],
            'landfall_windspeed':None,
            'max_observed_windspeed':None,
            'est_stormsurge':None,
            'max_stormsurge_adam':None,
            'rainfall_report_adam':None,
            'wind_report_adam':None,
            'gdacs_alert_level_adam':None,
            'countries_adam':None,
            'subnational_impacts_adam':None,
            'watches_noaa':s['country_watches'],
            'warnings_noaa':s['country_warnings'],
            'windforecast_noaa':s['windforecast_noaa'],
            'summary_link_noaa':s['summary'],
            'summary_noaa':text,
            'current_position':None,
            'report_date_noaa': str(pd.to_datetime(s['summary_date'])),
            'report_date_adam':None   
        },
        'subhazards':get_subhazards()
    }
    adam = get_adam()
    if adam: 
        for a in adam:
            if s['nhc_name'].lower() in a['name'].lower():
                storm_data['storm_data']['max_stormsurge_adam'] = a['max_storm_surge']
                storm_data['storm_data']['rainfall_report_adam'] = a['url']['rainfall']
                storm_data['storm_data']['gdacs_alert_level_adam'] = a['alert_level']
                storm_data['storm_data']['countries_adam'] = a['countries']
                storm_data['storm_data']['subnational_impacts_adam'] = a['url']['population']
                storm_data['storm_data']['report_date_adam'] = str(pd.to_datetime(a['published_at']))
                storm_data['storm_data']['current_position'] = (a['latitude'],a['longitude'])
    else: print('no adam data retrieved.')
    storm_data['storm_data']['report_date_aaastorms'] = str(pd.Timestamp.now())
    return storm_data
    

#%%
