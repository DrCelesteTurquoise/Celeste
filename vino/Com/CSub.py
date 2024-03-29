# ClientSub

import zmq

def create():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")  # 连接到服务器的地址

    # 订阅所有消息
    socket.subscribe(b"")

    print("已连接到服务器...")

    while True:
        # 接收消息
        message = socket.recv_string()
        print("收到消息: ", message)

if __name__ == "__main__":
    create()
