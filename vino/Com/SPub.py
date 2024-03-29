# ServerPub

import zmq

def create():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")

    print("等待订阅者连接...")

    while True:
      topic = input("Topic: ")
      message = input("CMD: ")
  
      socket.send_multipart([topic.encode(), message.encode()])
      print("Published Message: ", topic, message)

if __name__ == "__main__":
    create()
