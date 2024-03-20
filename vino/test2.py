
import sys
import time
import zmq
import os


Entity_name = "ChemXXX"

print(f"{Entity_name} Start")

context = zmq.Context()
sub = context.socket(zmq.SUB)
pub = context.socket(zmq.PUB)

try:
    sub.connect("tcp://localhost:5555")
    sub.setsockopt_string(zmq.SUBSCRIBE, Entity_name)
    pub.bind("tcp://*:5513")
    print(f"{Entity_name} Connected to the Host")
except:
    sub.close()
    pub.close()
    context.term()
    print(f"{Entity_name}Connection Fail")
else:
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