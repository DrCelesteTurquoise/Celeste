# SDL in ANL Entity MiR250 Version 1.0 by TDai

import sys
import time
import zmq
import os

import requests
import json

ip = '192.168.12.20'
host = 'http://' + ip + '/api/v2.0.0/'

headers = {}
headers['Content-Type'] = 'application/json'
headers['Authorization'] = 'Basic RGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA=='

        
def mission_status_template(host):
    url = 'status'
    get_request = requests.get(host+url)
    status_code = get_request.status_code
    if status_code == 200:
        txt = get_request.text
        status_dict = json.loads(txt)
        
        battery_percentage = float(status_dict.get('battery_percentage'))
        state = str(status_dict.get('state_text'))
        
        print('Battery Percentage:', int(battery_percentage))
        print('Status:', state)
    else:
        print('MiRError:', status_code)
        
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


def start_entity_MiR(Entity_name, sub_addr, sub_port, pub_addr, pub_port):
    print(f"{Entity_name} Start")

    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    pub = context.socket(zmq.PUB)

    try:
        sub.connect(f"tcp://{sub_addr}:{sub_port}")
        sub.setsockopt_string(zmq.SUBSCRIBE, Entity_name)
        pub.bind(f"tcp://{pub_addr}:{pub_port}")
        print(f"{Entity_name} Connected to the Host")
    except zmq.ZMQError as e:
        sub.close()
        pub.close()
        context.term()
        print(f"{Entity_name} Connection Fail: {e}")
        return

    while True:
        topic, cmd = sub.recv_multipart()
        print(topic.decode(), cmd.decode())
        cmd = cmd.decode()
        if cmd == 'GPC':
                        
            mission_id = {"mission_id": "b0a59fbe-e87e-11ee-a42c-00012978ede1"} #TDaiGPC
            requests.post(host + 'mission_queue', json = mission_id, headers = headers)
            
            # mission complete check every three secs
            mission_complete_check(host)           
            time.sleep(1)
            
            pub.send_string(f'{Entity_name}: To GPC Completed\n')
            print(f'{Entity_name} To GPC Completed\n')
        elif cmd == 'Charger':
            
            mission_id = {"mission_id": "099a22b7-e878-11ee-a42c-00012978ede1"} #TDaiCharger
            requests.post(host + 'mission_queue', json = mission_id, headers = headers)
            
            # mission complete check every three secs
            mission_complete_check(host)           
            time.sleep(1)
            
            pub.send_string(f'{Entity_name}: To Charger Completed\n')
            print(f'{Entity_name} To Charger Completed\n')
        elif cmd == '3':
            pub.send_string(f'{Entity_name} 3 Completed\n')
        else:
            print('Error! Plz rerun this file. Exit in 3 secs')
            pub.send_string(f'{Entity_name} Error in Host Command\n')
            time.sleep(3)
            sys.exit(1)

if __name__ == "__main__":
    Entity_name = "MiR250"
    sub_addr = "localhost"
    sub_port = "5555"
    pub_addr = "*"
    pub_port = "5515"
    start_entity_MiR(Entity_name, sub_addr, sub_port, pub_addr, pub_port)
