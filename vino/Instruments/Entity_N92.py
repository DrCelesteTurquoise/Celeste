# SDL in ANL Entity N9_2 Version 1.0 by TDai

import sys
import time
import zmq
import os

def start_entity_N92(Entity_name, sub_addr, sub_port, pub_addr, pub_port):
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
        if cmd == '1':
            time.sleep(4)
            pub.send_string(f'{Entity_name} 1 Completed\n')
            print(f'{Entity_name} 1 Completed\n')
        elif cmd == '2':
            time.sleep(4)
            pub.send_string(f'{Entity_name} 2 Completed\n')
        elif cmd == '3':
            pub.send_string(f'{Entity_name} 3 Completed\n')
        else:
            print('Error! Plz rerun this file. Exit in 3 secs')
            pub.send_string(f'{Entity_name} Error in Host Command\n')
            time.sleep(3)
            sys.exit(1)

if __name__ == "__main__":
    Entity_name = "N92"
    sub_addr = "192.168.12.246"
    sub_port = "56666"
    pub_addr = "192.168.12.246"
    pub_port = "56686"
    start_entity_N92(Entity_name, sub_addr, sub_port, pub_addr, pub_port)
