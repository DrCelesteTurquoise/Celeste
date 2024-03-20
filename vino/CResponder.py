# ClientResponder

import zmq

def create():
    context = zmq.Context()
    responder = context.socket(zmq.REP)
    responder.bind("tcp://*:5555")
    
    while True:
        # 等待请求
        request = responder.recv_string()
        print(f"Received request: {request}")
    
        # 处理请求（这里简单地回复一个消息）
        response = "Hello, this is the responder."
        responder.send_string(response)

if __name__ == "__main__":
  create()
