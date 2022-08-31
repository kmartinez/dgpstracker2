#author: Ioannis Christou
#
# desc: Finds the highest duration of a SWARM satellite pass for the next day.
#
# Can be extended by storing the pointers (of next day only) in an array and sorting them by Duration
# The 3-5 top recommendations can be sent to the SWARM unit
# Swarm unit saves the 3-5 time periods, starts 15 mins before midpoint of availability window
# ends 15 minutes after midpoint unless all the data has been sent successfully (no unsent messages)
# 
#
# Suggestion: Run on Raspberry Pi, make it sleep for 1hr, wake up to check if the current datetime
# is the same as previously stored one, if it's not carry out the pass checks and send to
# beehive

from string import Template
from datetime import date
from datetime import timedelta
from datetime import datetime
import os
import time
import requests
import json
import math


templ_api_url="https://bumblebee.hive.swarm.space/api/v1/passes?\
lat=$x&\
lon=$y&\
alt=$z"

today = date.today()

next_day = today + timedelta(days=1)

def get_seconds(hh_mm_ss):
    dur = hh_mm_ss.split(":")
    hrs = int(dur[0])
    mins = int(dur[1])
    secs = int(dur[2])
    tot_secs = hrs*3600 + mins * 60 + secs
    return tot_secs

# def seconds_to_time(max_dur):
#     ## turn duration back into hh:mm:ss
#     if(max_dur)>=3600:
#         hrs_float = max_dur/3600
#         mins_float, hrs = math.modf(hrs_float)
#         mins = mins_float*60
#         secs_float, mins = math.modf(mins)
#         secs = secs_float*60
#         #remainder = max_dur%3600
#     elif(max_dur>=60):
#         hrs = 0
#         mins_float = max_dur/60
#         secs_float, mins = math.modf(mins_float)
#         secs = secs_float*60
#     else:
#         hrs = 0
#         mins = 0
#         secs = max_dur
#     return hrs, mins, secs

def get_pass_info(api_url):
    response = requests.get(api_url)
    json_response = json.loads(response.text)
   # print(json_response["passes"])
    get_highest_dur(json_response["passes"])


def get_highest_dur(data):
    max_dur = 0
    max_dur_secs = 0
    pointer = -1
    for index, obj in enumerate(data):
        start_date = obj['start_pass'].split("T")[0]#.split("-")
        #print(start_date)
        start_date = datetime.strptime(start_date,'%Y-%m-%d').date()
        if(start_date == next_day):
            print(start_date)
            dur = get_seconds(obj['duration'])
            if (dur > max_dur_secs):
                max_dur_secs = dur
                max_dur = obj['duration']
                pointer = index
    
    #hh, mm , ss = seconds_to_time(max_dur)

    #print("Maximum duration: {}:{}:{}, Pointer: {}".format(hh, mm, ss,pointer))
    print("Maximum duration: {}, Pointer: {}".format(max_dur,pointer))
    print("Start time: {}, End time: {}, Duration: {}".format(data[pointer]['start_pass'], data[pointer]['end_pass'], max_dur))

def beehive_post(data):
    #TODO: POST best time periods to beehive
    return

def main():

    ## Check current date
    ## Make sure the !next! day's highest duration is determined
    ## not current one's

    lat = 64.012589
    long = -16.422405
    alt = 5

    api_url = Template(templ_api_url).substitute(x = str(lat), y = str(long), z = str(alt))

    print(api_url)
    
    while True:
    
        if(date.today() > today):
            today = date.today()
            get_pass_info(api_url)

            #TODO: Send best availability data to the beehive
            #TODO: Find 3-5 best availability time periods


        time.sleep(3600)
    
    ## Choose latitude, longitude, altitude values:
    
    # lat = input("Enter latitude x (decimal degrees): ")
    # long = input("Enter longitude y (decimal degrees): ")
    # alt = input("Enter altitude z (metres): ")

if __name__=="__main__":
    main() 