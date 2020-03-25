
 # (c) Mika Mäkelä - 2020
 # AWS Lambda backend for the ESP8266 E-paper (e-ink) dashboard project.

import json
import urllib3
import xml.etree.ElementTree as ET
import datetime
from random import randint
from random import seed
import os

http = urllib3.PoolManager()
adafruitkey = os.environ['adafruitkey']
adafruituri = os.environ['adafruituri']
fbtoken = os.environ['fbtoken']
fbgroupid = os.environ['fbgroupid']

def lambda_handler(event, context):
   
    fmi_time_delta = datetime.datetime.now() - datetime.timedelta(minutes=15)
    fmi_time = fmi_time_delta.replace(microsecond=0).isoformat()
    fmi_url_observation = 'http://opendata.fmi.fi/wfs?request=getFeature&storedquery_id=fmi::observations::weather::simple&place=malmi,helsinki&maxlocations=1&starttime={0}&parameters=t2m,rh,ws_10min,wg_10min'.format(fmi_time)
    fmi_url_forecast = 'http://opendata.fmi.fi/wfs?request=getFeature&storedquery_id=fmi::forecast::hirlam::surface::point::simple&place=malmi,helsinki&timestep=60&maxlocations=1&parameters=temperature'

    print(fmi_url_observation)

    responseBody = {
        **fetch_fmi_observation(fmi_url_observation),
        **fetch_fmi_forecast(fmi_url_forecast),
        **fetch_adafruit(),
        'rss':fetch_rss()
    }

    return {
        'statusCode': 200,
        'body': json.dumps(responseBody,  ensure_ascii=False)
    }


def fetch_fb():
    fb_url = 'https://graph.facebook.com/{0}/feed?access_token={1}'.format(fbgroupid,fbtoken)
    
    fb_response = http.request('GET', fb_url)
    fb_data = json.loads(fb_response.data)
    
    fb_messages = []
    fb_messages.append('Facebook')
    
    for m in fb_data['data']:
        if 'message' in m:
            fb_messages.append(m['message'].replace('ä', 'a').replace('ö','o'))

    return fb_messages


def fetch_fmi_observation(fmi_url_observation):
    parRhTime = None
    parRhValue = None
    parTempTime = None
    parTempValue = None
    parWS10Value = None
    parWG10Value = None

    # HTTP Request FMI Observation 
    fmi_response_obs = http.request('GET', fmi_url_observation)
    fmi_xml_data_obs = fmi_response_obs.data
    fmi_root_obs = ET.fromstring(fmi_xml_data_obs)
        
    for members in fmi_root_obs.findall('{http://www.opengis.net/wfs/2.0}member'):
        for member in members.findall('{http://xml.fmi.fi/schema/wfs/2.0}BsWfsElement'):
            
            parName = member.find('{http://xml.fmi.fi/schema/wfs/2.0}ParameterName')
            
            if parName.text == 'rh':
                parRhTime = member.find('{http://xml.fmi.fi/schema/wfs/2.0}Time').text
                parRhValue = member.find('{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue').text
                
            if parName.text == 't2m':
                parTempValue = member.find('{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue').text
                
            if parName.text == 'ws_10min':
                parWS10Value = member.find('{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue').text

            if parName.text == 'wg_10min':
                parWG10Value = member.find('{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue').text


    retval = None
    
    try:
        retval = {
            'tempOut':float(parTempValue),
            'rhOut':round(float(parRhValue)),
            'ws10Out':round(float(parWS10Value)),
            'wg10Out':round(float(parWG10Value))
        }
    except Exception:
        retval = {
            'tempOut':0,
            'rhOut':0,
            'ws10Out':0,
            'wg10Out':0
        }
        
    return retval


def fetch_fmi_forecast(fmi_url_forecast):
    parTemp6hValue = None
    parTemp12hValue = None
    parTemp24hValue = None

    # HTTP Request FMI Forecast 
    fmi_response_forecast = http.request('GET', fmi_url_forecast)
    fmi_xml_data_forecast = fmi_response_forecast.data
    fmi_root_forecast = ET.fromstring(fmi_xml_data_forecast)
    
    itemcount = 0
    
    for members in fmi_root_forecast.findall('{http://www.opengis.net/wfs/2.0}member'):
        for member in members.findall('{http://xml.fmi.fi/schema/wfs/2.0}BsWfsElement'):
            
            itemcount = itemcount + 1

            parName = member.find('{http://xml.fmi.fi/schema/wfs/2.0}ParameterName')

            if parName.text == 'temperature' and itemcount == 7:
                parTemp6hValue = member.find('{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue').text
                
            if parName.text == 'temperature' and itemcount == 13: 
                parTemp12hValue = member.find('{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue').text
                
            if parName.text == 'temperature' and itemcount == 25: 
                parTemp24hValue = member.find('{http://xml.fmi.fi/schema/wfs/2.0}ParameterValue').text

    return {
        'temp6h':round(float(parTemp6hValue), 1),
        'temp12h':round(float(parTemp12hValue), 1),
        'temp24h':round(float(parTemp24hValue), 1)
    }


def fetch_rss():

    rss_urls = []
    
    rss_urls.append(['Kauppalehti','https://feeds.kauppalehti.fi/rss/main'])
    #rss_urls.append(['Helsingin Sanomat','https://www.hs.fi/rss/teasers/etusivu.xml'])
    rss_urls.append(['Iltalehti','https://www.iltalehti.fi/rss/rss.xml'])
    #rss_urls.append(['Tekniikka ja Talous','https://www.tekniikkatalous.fi/api/feed/v2/rss/tt'])
    #rss_urls.append(['Yle luetuimmat','https://feeds.yle.fi/uutiset/v1/mostRead/YLE_UUTISET.rss'])
    rss_urls.append(['Yle paauutiset','https://feeds.yle.fi/uutiset/v1/majorHeadlines/YLE_UUTISET.rss'])  
    
    #rss_urls.append(['Yle Uusimaa','https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_UUTISET&concepts=18-147345'])
  
    randomint = randint(0, 3)
    
    if randomint == 3:
        return fetch_fb()
    else:
        rss_final = rss_urls[randomint]
    
        rss_response = http.request('GET', rss_final[1])
        rss_xml_data = rss_response.data.decode('utf-8')
        
        #entire feed
        rss_root = ET.fromstring(rss_xml_data)
        rss_item = rss_root.findall('channel/item')
    
        rss_feed = []
    
        count = 0
        
        rss_feed.append(rss_final[0])
        
        for entry in rss_item:
            count += 1
            title = entry.findtext('title')  
            rss_feed.append(title.replace('ä', 'a').replace('ö','o'))
    
            if count > 5:
                break
    
        return rss_feed
            

def fetch_adafruit():

    adafruit_temp_value = 0
    adafruit_rh_value = 0
    adafruit_tulo_temp_value = 0
    adafruit_tulo_rh_value = 0
    
    adafruit_header = {'X-AIO-Key': adafruitkey}
    adafruit_temp_url = '{0}/temperature/data/last'.format(adafruituri)
    adafruit_rh_url = '{0}/humidity/data/last'.format(adafruituri)
    adafruit_tulo_temp_url = '{0}/temperaturesauna/data/last'.format(adafruituri)
    adafruit_tulo_rh_url = '{0}/humiditysauna/data/last'.format(adafruituri)

    adafruit_response = http.request('GET', adafruit_temp_url, headers = adafruit_header)
    adafruit_data = adafruit_response.data
    adafruit_temp_value = json.loads(adafruit_data)['value']
        
    adafruit_response = http.request('GET', adafruit_rh_url, headers = adafruit_header)
    adafruit_data = adafruit_response.data
    adafruit_rh_value = json.loads(adafruit_data)['value']

    adafruit_response = http.request('GET', adafruit_tulo_temp_url, headers = adafruit_header)
    adafruit_data = adafruit_response.data
    adafruit_tulo_temp_value = json.loads(adafruit_data)['value']

    adafruit_response = http.request('GET', adafruit_tulo_rh_url, headers = adafruit_header)
    adafruit_data = adafruit_response.data
    adafruit_tulo_rh_value = json.loads(adafruit_data)['value']

    return {
        'tempIn':round(float(adafruit_temp_value), 1),
        'rhIn':round(float(adafruit_rh_value)),
        'tempTulo':round(float(adafruit_tulo_temp_value), 1),
        'rhTulo':round(float(adafruit_tulo_rh_value))
    }
