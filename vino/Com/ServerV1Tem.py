# ServerPub

import time
import zmq

def start_server(pub_addr, pub_port, sub_addr, sub_port):
    context = zmq.Context()
    pub = context.socket(zmq.PUB)
    pub.bind(f"tcp://{pub_addr}:{pub_port}")

    sub = context.socket(zmq.SUB)
    sub.connect(f"tcp://{sub_addr}:{sub_port}")
    sub.subscribe(b"")

    while True:
      topic = input("Topic: ")
      message = input("CMD: ")

      pub.send_multipart([topic.encode(), message.encode()])
      print("Published Message: ", topic, message)

      feedback = sub.recv_string()
      print(feedback)

if __name__ == "__main__":
    pub_addr = "*"
    pub_port = "5555"
    sub_addr = "localhost"
    sub_port = "5515"
    start_server(pub_addr, pub_port, sub_addr, sub_port)
