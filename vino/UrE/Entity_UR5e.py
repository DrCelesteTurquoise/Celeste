# SDL in ANL Entity UR5e Version 1.0 by TDai

import sys
import time
import zmq
import os
import socket
import logging

# UR5eIP default ip = '192.168.12.249'

class UR5eRemote:
    def __init__(self, robotIP):
        self.robotIP = robotIP
        self.port = 29999
        self.timeout = 5
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.getLogger().setLevel(logging.INFO)

    def connect(self):
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.robotIP, self.port))
        self.sock.recv(1096)

    def sendAndReceive(self, command):
        try:
            self.sock.sendall((command + '\n').encode())
            return self.get_reply()
        except (ConnectionResetError, ConnectionAbortedError):
            logging.warning('The connection was lost to the robot. Please connect and try running again.')
            self.close()
            sys.exit()

    def get_reply(self):
        """
        read one line from the socket
        :return: text until new line
        """
        collected = b''
        while True:
            part = self.sock.recv(1)
            if part != b"\n":
                collected += part
            elif part == b"\n":
                break
        return collected.decode("utf-8")
    
    def program_complete_check(self):
        while True:
            time.sleep(3)
            state = self.sendAndReceive('programState')
            
            if 'STOPPED' in state:
                break       
            else:
                continue

    def close(self):
        self.sock.close()



def start_entity_UR5e(Entity_name, sub_addr, sub_port, pub_addr, pub_port, ur5e_ip):
    print(f"{Entity_name} Start")

    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    pub = context.socket(zmq.PUB)
    
    ur5eremote = UR5eRemote(ur5e_ip)

    try:
        sub.connect(f"tcp://{sub_addr}:{sub_port}")
        sub.setsockopt_string(zmq.SUBSCRIBE, Entity_name)
        pub.bind(f"tcp://{pub_addr}:{pub_port}")
        print(f"{Entity_name} Connected to the Host")
        
        ur5eremote.connect()
        remoteCheck = ur5eremote.sendAndReceive('is in remote control')
        if 'false' in remoteCheck:
            logging.warning('Robot is in local mode. Some commands may not function.')
        
    except zmq.ZMQError as e:
        sub.close()
        pub.close()
        context.term()
        
        ur5eremote.close()
        
        print(f"{Entity_name} Connection Fail: {e}")
        return

    while True:
        topic, cmd = sub.recv_multipart()
        print(topic.decode(), cmd.decode())
        cmd = cmd.decode()
        if cmd == 'TDai':
            
            ur5eremote.sendAndReceive('load TDai.urp')
            time.sleep(2)
            ur5eremote.sendAndReceive('play')
            ur5eremote.program_complete_check()
            time.sleep(1)
            
            pub.send_string(f'{Entity_name} Action TDai Completed\n')
            print(f'{Entity_name} Action TDai Completed\n')
        elif cmd == 'TDai2':
            ur5eremote.sendAndReceive('load TDai2.urp')
            time.sleep(2)
            ur5eremote.sendAndReceive('play')
            ur5eremote.program_complete_check()
            time.sleep(1)
            
            pub.send_string(f'{Entity_name} Action TDai2 Completed\n')
            print(f'{Entity_name} Action TDai2 Completed\n')
        elif cmd == 'TDai3':
            ur5eremote.sendAndReceive('load TDai3.urp')
            time.sleep(2)
            ur5eremote.sendAndReceive('play')
            ur5eremote.program_complete_check()
            time.sleep(1)
            
            pub.send_string(f'{Entity_name} Action TDai3 Completed\n')
            print(f'{Entity_name} Action TDai3 Completed\n')
        else:
            print('Error! Plz rerun this file. Exit in 3 secs')
            pub.send_string(f'{Entity_name} Error in Host Command\n')
            time.sleep(3)
            sys.exit(1)

if __name__ == "__main__":
    Entity_name = "UR5e"
    sub_addr = "localhost"
    sub_port = "5555"
    pub_addr = "*"
    pub_port = "5515"
    ur5e_ip = '192.168.12.249'
    start_entity_UR5e(Entity_name, sub_addr, sub_port, pub_addr, pub_port, ur5e_ip)
