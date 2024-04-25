import zmq
import time

# ZeroMQ setup
context = zmq.Context()
socket = context.socket(zmq.PUB)
# socket.connect("tcp://localhost:5555")
socket.bind("tcp://*:5556")

client_context = zmq.Context()
client_socket = client_context.socket(zmq.SUB)
client_socket.connect("tcp://localhost:5555")
client_socket.setsockopt_string(zmq.SUBSCRIBE, "")

while True:
    message = client_socket.recv_string()
    topic, command = message.split()
    # print(f"Received command '{command}' for topic '{topic}'. Sending response...")
    # 在这里添加你的处理逻辑
    # 这里只是简单地回复一条消息
    response = f"Response to command '{command}' for topic '{topic}'"
    time.sleep(5)
    socket.send_string(response)
    print("Response sent:", response)
