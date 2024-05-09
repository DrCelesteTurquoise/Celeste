import requests, json, time

# test push from local TDai and test if the name is correct
# why there is no response

# get request
ip = '192.168.12.20'
host = 'http://' + ip + '/api/v2.0.0/'

# format headers
headers = {}
headers['Content-Type'] = 'application/json'
headers['Authorization'] = 'Basic RGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA=='

def mission_complete_check(host):
    
    while True:
        # check every 3 sec 
        time.sleep(3)
        url = 'status'
        get_request = requests.get(host+url)
        txt = get_request.text
        status_dict = json.loads(txt)        
        state = str(status_dict.get('state_text'))
        
        if state == 'Ready':
            break       
        else:
            continue


# mission_id = {"mission_id": "b0a59fbe-e87e-11ee-a42c-00012978ede1"} #TDaiGPC
# requests.post(host + 'mission_queue', json = mission_id, headers = headers)
'''
mission_id = {"mission_id": "099a22b7-e878-11ee-a42c-00012978ede1"} #TDaiCharger
requests.post(host + 'mission_queue', json = mission_id, headers = headers)

mission_complete_check(host)

print('Complete')

'''

""" url = 'status'
get_request = requests.get(host+url)
status = get_request.status_code
if status == 200:
    txt = get_request.text
    status_dict = json.loads(txt)
    
    battery_percentage = float(status_dict.get('battery_percentage'))
    battery_str = 'Battery Per: %.lf' %battery_percentage
    
    state = str(status_dict.get('state_text'))
    #IbI1['text'] = state
    
    print(battery_str)
    print('Battery Percentage:', int(battery_percentage))
    print('Status:', state) """


### this is how we remote get mir info

#get_status = requests.get(host + 'status', headers = headers)

#print(get_status.text)



#get_position_types = requests.get(host + 'position_types', headers = headers)

#print(get_position_types.text)

get_missions = requests.get(host + 'missions', headers = headers)

print(get_missions.text)

### this is how we remote control the mir

# mission_id = {"mission_id": "b0a59fbe-e87e-11ee-a42c-00012978ede1"} #TDaiGPC
# post_mission = requests.post(host + 'mission_queue', json = mission_id, headers = headers)

# print(post_mission)

# mission_id = {"mission_id": "099a22b7-e878-11ee-a42c-00012978ede1"} #TDaiCharger
# post_mission = requests.post(host + 'mission_queue', json = mission_id, headers = headers)

# print(post_mission)

