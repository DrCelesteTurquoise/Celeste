import requests, json

# test push from local TDai and test if the name is correct
# why there is no response

# get request
ip = '192.168.12.20'
host = 'http://' + ip + '/api/v2.0.0/'

# format headers
headers = {}
headers['Content-Type'] = 'application/json'
headers['Authorization'] = 'Basic RGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA=='

### this is how we remote get mir info

get_position_types = requests.get(host + 'position_types', headers = headers)

print(get_position_types.text)

#get_missions = requests.get(host + 'missions', headers = headers)

#print(get_missions.text)

### this is how we remote control the mir

# mission_id = {"mission_id": "b0a59fbe-e87e-11ee-a42c-00012978ede1"} #TDaiGPC
# post_mission = requests.post(host + 'mission_queue', json = mission_id, headers = headers)

# print(post_mission)

# mission_id = {"mission_id": "099a22b7-e878-11ee-a42c-00012978ede1"} #TDaiCharger
# post_mission = requests.post(host + 'mission_queue', json = mission_id, headers = headers)

# print(post_mission)

