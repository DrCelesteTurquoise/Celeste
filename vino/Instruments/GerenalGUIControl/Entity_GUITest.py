# SDL in ANL Entity GUI Control Template Version 1.0 by TDai

import sys
import time
import zmq
import os

# cmd java -jar C:\NFTT\BTC\Test/sikulixide-2.0.5.jar -p

from TDaiGUIControl import *
import py4j
import glob

def start_entity_GUIControl(Entity_name, sub_addr, sub_port, pub_addr, pub_port):
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
        if cmd == 'WF1':
            
            
            time.sleep(6)
            addImagePath(r'C:\NFTT\BTC\Test\pic')
            scr=Screen()    
            file_out_dir = r'C:\NFTT\BTC\Test\pic\\'
            id_file = file_out_dir + '*.png'
            
            for img in glob.glob(id_file):
                print(img)
            
                #match = scr.exists(img, 3.) # method missing, wrong signature
                match = scr.exists(img, 3.0) # number must be float/double
                if match:
                    #match.highlight(2)
                    match.click()
                    # match.type(img,"lilili\n\n")
            
            pub.send_string(f'{Entity_name} SimulationDemo Completed\n')
            print(f'{Entity_name} SimulationDemo Completed\n')
        elif cmd == 'WF2':
            
            
            pub.send_string(f'{Entity_name} CappingDemo Completed\n')
            print(f'{Entity_name} CappingDemo Completed\n')
        elif cmd == 'WF3':
            pub.send_string(f'{Entity_name} 3 Completed\n')
        else:
            print('Error! Plz rerun this file. Exit in 3 secs')
            pub.send_string(f'{Entity_name} Error in Host Command\n')
            time.sleep(3)
            sys.exit(1)

if __name__ == "__main__":
    Entity_name = "KLA"
    sub_addr = "192.168.12.247"
    sub_port = "56666"
    pub_addr = "192.168.12.248"
    pub_port = "5636"
    start_entity_GUIControl(Entity_name, sub_addr, sub_port, pub_addr, pub_port)