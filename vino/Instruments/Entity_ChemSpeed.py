# SDL in ANL Entity ChemSpeed Version 1.0 by TDai

import sys
import time
import zmq
import os

def start_entity_ChemSpeed(Entity_name, sub_addr, sub_port, pub_addr, pub_port):
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
        if cmd == 'SimDemo':
            
            app_dir = r'C:\Users\Operator\Desktop\AutoWF\ChemBat\SimChemTDai.bat'
            os.startfile(app_dir)
            fp = open(r'C:\Users\Operator\Desktop\AutoWF\start\1.txt', 'x')
            fp.close()

            while True:
                if os.path.exists(r'C:\Users\Operator\Desktop\AutoWF\finished\1.txt'):
                    time.sleep(1)
                    break
                else:
                    time.sleep(1)
                    #print('Busy')
            os.remove(r'C:\Users\Operator\Desktop\AutoWF\finished\1.txt')
            
            pub.send_string(f'{Entity_name} SimulationDemo Completed\n')
            print(f'{Entity_name} SimulationDemo Completed\n')
        elif cmd == 'CapDemo':
            
            app_dir = r'C:\Users\Operator\Desktop\AutoWF\ChemBat\CappingDemo.bat'
            os.startfile(app_dir)
            fp = open(r'C:\Users\Operator\Desktop\AutoWF\start\1.txt', 'x')
            fp.close()

            while True:
                if os.path.exists(r'C:\Users\Operator\Desktop\AutoWF\finished\1.txt'):
                    time.sleep(1)
                    break
                else:
                    time.sleep(1)
                    #print('Busy')
            os.remove(r'C:\Users\Operator\Desktop\AutoWF\finished\1.txt')
            
            pub.send_string(f'{Entity_name} CappingDemo Completed\n')
            print(f'{Entity_name} CappingDemo Completed\n')
        elif cmd == '3':
            pub.send_string(f'{Entity_name} 3 Completed\n')
        else:
            print('Error! Plz rerun this file. Exit in 3 secs')
            pub.send_string(f'{Entity_name} Error in Host Command\n')
            time.sleep(3)
            sys.exit(1)

if __name__ == "__main__":
    Entity_name = "ChemSpeed"
    sub_addr = "192.168.12.246"
    sub_port = "56666"
    pub_addr = "192.168.12.230"
    pub_port = "56636"
    start_entity_ChemSpeed(Entity_name, sub_addr, sub_port, pub_addr, pub_port)