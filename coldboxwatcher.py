#!/usr/bin/env python3

'''
Coldboxwatcher.py will follow the temperature of a DS18B20 temperature probe
and report changes in temperature when outside allowed range using a Slack webhook
'''

import json
import requests
import os,glob,time
import privatewebhookurl # this file should just contain the line "webhook_url = 'https://hooks.slack.com/services/.....'
import datetime

def sendwebhook(text):
    # Set the webhook_url to the one provided by Slack when you create the webhook at https://my.slack.com/services/new/incoming-webhook/
    # webhooks have the form shown below - they should be kept private. The webhook URL below is not valid
    # webhook_url = 'https://hooks.slack.com/services/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'
    #privatewebhookurl.webhook_url
    
    
    slack_data = {'text': text, 'channel': '#webhooktest', 'username': 'ColdBoxWatcher','toxen': 'abcd', 'icon_url': 'https://www.flaticon.com/free-icon/circuit-board_1457527'}
    #others "token, channel, text, icon_url, username, blocks'
    
    response = requests.post(privatewebhookurl.webhook_url, data=json.dumps(slack_data),headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        print('ug')
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
            )

class DS18B20:
	# much of this code is lifted from Adafruit web site
	# This class can be used to access one or more DS18B20 temperature sensors
	# It uses OS supplied drivers and one wire support must be enabled
	# To do this add the line
	# dtoverlay=w1-gpio
	# to the end of /boot/config.txt
	#
	# connect ground wire to GPIO ground
	# connect signal wire to GPIO 4 *and* GPIO 3.3V via a 4k8 (4800 ohm) pullup resistor
	# connect Vcc wire to GPIO 3.3V
	# You can connect more than one sensor to the same set of pins
	# Only one pullup resistor is required
	
	def __init__(self):
            # load required kernel modules
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            # Find file names for the sensor(s)
            base_dir = '/sys/bus/w1/devices/'
            device_folder = glob.glob(base_dir + '28*')
            self._num_devices = len(device_folder)
            self._device_file = list()
            i = 0
            while i < self._num_devices:
                self._device_file.append(device_folder[i] + '/w1_slave')
                i += 1
		
	def _read_temp(self,index):
            # Issue one read to one sensor
            # you should not call this directly
            f = open(self._device_file[index],'r')
            lines = f.readlines()
            f.close()
            return lines
        		
	def tempC(self,index = 0):
            # call this to get the temperature in degrees C
            # detected by a sensor
            lines = self._read_temp(index)
            retries = 5
            while (lines[0].strip()[-3:] != 'YES') and (retries > 0):
                # read failed so try again
                time.sleep(0.1)
                #print('Read Failed', retries)
                lines = self._read_temp(index)
                retries -= 1
	    
            if retries == 0:
                return 998
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp = lines[1][equals_pos + 2:]			
                return float(temp)/1000
            else:
	        # error
                return 999
			
	def device_count(self):
	    # call this to see how many sensors have been detected
	    return self._num_devices

# set upper and lower bounds for coldbox here


up_bnd = 26 # high temperature danger range
low_bnd = 21 # low temperature danger range

startupslacktext = '{} {} {} {} {}{}'.format('I have started watching and will warn if temperature outside range',
                                             low_bnd,'to',up_bnd,u'\N{DEGREE SIGN}','C')
print(startupslacktext)
sendwebhook(startupslacktext)
weekno_prev=100 # weekno goes between 0 [monday] to 6 [sunday]

temp_prev=0
while True:
    x = DS18B20()
    temp=x.tempC(0)
    temp_rnd=round(temp)
    weekno = datetime.datetime.today().weekday()
    if weekno != weekno_prev:
        regulartext = '{} {}{}{}'.format('I am watching. Current temperature is',temp_rnd,u'\N{DEGREE SIGN}','C')
        sendwebhook(regulartext)
    text = '{} {} {} {} {} {} {} {} {} {}'
    print(text.format('raw:',str(temp),'rnd:',str(temp_rnd),'prev:',str(temp_prev),
                      'upperbound:',str(up_bnd),'lowerbound:',str(low_bnd)))
    if temp_rnd != temp_prev and temp_rnd >= up_bnd or temp_rnd <= low_bnd:
        print('sending a warning to Slack')
        warningtext='{} {}{}{}'.format('Coldbox temperature is out of allowed range at',str(temp_rnd),u'\N{DEGREE SIGN}','C')
        sendwebhook(warningtext)
    temp_prev = temp_rnd
    weekno_prev = weekno
    time.sleep(1)
    
   
## test temperature sensors
#x = DS18B20()
#count=x.device_count()
#print(count)
#i = 0
#while i < count:
#    print(x.tempC(i))
#    temperature=x.tempC(i)
#    i += 1


