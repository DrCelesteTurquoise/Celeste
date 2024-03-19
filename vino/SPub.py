# ServerPub

import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")  # 绑定到端口 5555

print("等待客户端连接...")

while True:
    # 等待客户端请求
    message = socket.recv_string()
    print("收到请求: ", message)

    # 回复消息给客户端
    socket.send_string("服务端收到消息: {}".format(message))
