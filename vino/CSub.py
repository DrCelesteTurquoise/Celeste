# ClientSub

import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")  # 连接到服务器地址和端口

# 发送消息给服务器
message = "Hello, Server!"
socket.send_string(message)

# 等待服务器回复
reply = socket.recv_string()
print("从服务器收到回复: ", reply)
