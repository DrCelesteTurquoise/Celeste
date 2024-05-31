# SDL in ANL Entity UR5e Version 1.0 by TDai

import PySimpleGUI as sg
import sys
import time
import zmq
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



def configuration():

    sg.theme('Lightgreen')
    layout_configuration = [
        [sg.Text('ANL SDL UR5e Control Panel', font='Calibri 23 italic bold underline')],
        [sg.Text('Please finish UR5e Configuration:', font='Calibri 18')],
        
        [sg.Text('Entity_name', font='Calibri 13 italic bold'), sg.InputText(default_text='UR5e')],
        
        [sg.Text('sub_addr IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('sub_port Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56666)],
        [sg.Text('pub_addr IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('pub_port Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56626)],
        
        [sg.Button('OK&GO'), sg.Button('Exit')]]
    window_configuration = sg.Window('UR5e Configuration Launcher', layout_configuration, icon=r'C:\NFTT\BTC\Test\VINODDD\UR5e\UrEncapsulation\IMG\ur5e.ico')

    while True:
        event, values = window_configuration.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            sys.exit()
        Entity_name = values[0]
        sub_addr = values[1]
        sub_port = int(values[2])
        pub_addr = values[3]
        pub_port = int(values[4])

        break
    window_configuration.close()
    return Entity_name, sub_addr, sub_port, pub_addr, pub_port



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
        elif cmd == 'ToolChangeDemo':
            ur5eremote.sendAndReceive('load TDaiToolChangeDemo.urp')
            time.sleep(2)
            ur5eremote.sendAndReceive('play')
            ur5eremote.program_complete_check()
            time.sleep(1)
            
            pub.send_string(f'{Entity_name} Action ToolChangeDemo Completed\n')
            print(f'{Entity_name} Action ToolChangeDemo Completed\n')
        elif cmd == 'LoadVial2ChemS':
            ur5eremote.sendAndReceive('load TDaiLoadVial2ChemS.urp')
            time.sleep(2)
            ur5eremote.sendAndReceive('play')
            ur5eremote.program_complete_check()
            time.sleep(1)
            
            pub.send_string(f'{Entity_name} Action TDaiLoadVial2ChemS Completed\n')
            print(f'{Entity_name} Action TDaiLoadVial2ChemS Completed\n')
            
        elif cmd == 'Exit':          
            pub.send_string(f'{Entity_name}: Exit Completed\n')
            print(f'{Entity_name} Exit Completed\n')
            
            sub.close()
            pub.close()
            context.term()
            ur5eremote.close()
            time.sleep(1)
            sys.exit()  
            
        else:
            print('Error! Plz rerun this file. Exit in 3 secs')
            pub.send_string(f'{Entity_name} Error in Host Command\n')
            time.sleep(3)
            sys.exit(1)

if __name__ == "__main__":
    
    ur5e_ip = '192.168.12.249'
    Entity_name, sub_addr, sub_port, pub_addr, pub_port = configuration()
    start_entity_UR5e(Entity_name, sub_addr, sub_port, pub_addr, pub_port, ur5e_ip)
