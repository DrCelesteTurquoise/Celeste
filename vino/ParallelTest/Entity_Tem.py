import sys
import time
import zmq
import multiprocessing


def init(entity_name):
    print(f"{entity_name} Start")
    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    pub = context.socket(zmq.PUB)

    try:
        sub.connect('tcp://172.31.1.17:5558')
        sub.setsockopt_string(zmq.SUBSCRIBE, entity_name)
        pub.bind('tcp://172.31.1.16:5553')
        print(f"{entity_name} Connected to the Host")
        return sub, pub  # Return the sockets for later use
    except Exception as e:
        print(f'Connection Fail: {e}')
        return None, None


def monitorHost(sub, pub, context, entity_name, entity_state):
    if sub is None or pub is None:
        return

    print(f"{entity_name} Ready")
    while True:
        topic, cmd = sub.recv_multipart()
        print(topic.decode(), cmd.decode())
        cmd = cmd.decode()
        if cmd == '1':
            entity_state.value = 'Executing'
            pub.send_string(entity_state.value)
            time.sleep(3)
            entity_state.value = 'Ready'
            pub.send_string(entity_state.value)
        elif cmd == 'Exit':
            time.sleep(2)
            pub.send_string(f'{entity_name} Exit, Communication Close\n')
            pub.close()
            sub.close()
            context.term()
        else:
            print('Error! Plz rerun this file. Exit in 5 secs')
            pub.send_string(f'{entity_name} Error in Host Command\n')
            time.sleep(5)
            sys.exit(1)


def pubState(sub, pub, entity_state):
    if sub is None or pub is None:
        return

    print(f"{entity_name} pub its state")
    while True:
        if sub is None or pub is None:
            break
        time.sleep(60)
        pub.send_string(entity_state.value)


if __name__ == '__main__':
    entity_name = "Name"
    sub, pub, context = init(entity_name)
    if sub and pub:
        manager = multiprocessing.Manager()
        entity_state = manager.Value('s', 'Ready')  # 创建一个共享字符串变量，初始值为'Ready'

        monitor_process = multiprocessing.Process(target=monitorHost, args=(sub, pub, context, entity_state))
        pub_state_process = multiprocessing.Process(target=pubState, args=(sub, pub, entity_state))
        monitor_process.start()
        pub_state_process.start()
        monitor_process.join()
        pub_state_process.join()