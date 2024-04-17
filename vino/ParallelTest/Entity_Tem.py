import sys
import time
import zmq
import multiprocessing


def init(Entity_name):
    print(f"{Entity_name} Start")
    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    pub = context.socket(zmq.PUB)

    try:
        sub.connect('tcp://172.31.1.17:5558')
        sub.setsockopt_string(zmq.SUBSCRIBE, Entity_name)
        pub.bind('tcp://172.31.1.16:5553')
        print(f"{Entity_name} Connected to the Host")
        return sub, pub  # Return the sockets for later use
    except Exception as e:
        print(f'Connection Fail: {e}')
        return None, None


def monitorHost(sub, pub, ChemS_State):
    if sub is None or pub is None:
        return

    print("EntityChemS Waiting")
    while True:
        topic, cmd = sub.recv_multipart()
        print(topic.decode(), cmd.decode())
        cmd = cmd.decode()
        if cmd == '1':
            ChemS_State.value = 'Executing'
            pub.send_string(ChemS_State.value)
            time.sleep(3)
            ChemS_State.value = 'Waiting'
            pub.send_string(ChemS_State.value)
        elif cmd == 'Exit':
            time.sleep(2)
            pub.send_string('[ChemS] Exit Communication Close\n')
            pub.close()
            sub.close()
            context.term()
        else:
            print('Error! Plz rerun this file. Exit in 5 secs')
            pub.send_string('[ChemS] Error in Host Command\n')
            time.sleep(5)
            sys.exit(1)


def pubState(sub, pub, ChemS_State):
    if sub is None or pub is None:
        return

    print("EntityChemS pub its state")
    while True:
        if sub is None or pub is None:
            break
        time.sleep(60)
        pub.send_string(ChemS_State.value)


if __name__ == '__main__':
    sub, pub = init()
    if sub and pub:
        manager = multiprocessing.Manager()
        ChemS_State = manager.Value('s', 'Waiting')  # 创建一个共享字符串变量，初始值为'Waiting'

        monitor_process = multiprocessing.Process(target=monitorHost, args=(sub, pub, ChemS_State))
        pub_state_process = multiprocessing.Process(target=pubState, args=(sub, pub, ChemS_State))
        monitor_process.start()
        pub_state_process.start()
        monitor_process.join()
        pub_state_process.join()