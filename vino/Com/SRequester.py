# ServerRequester

import zmq

def create():
    context = zmq.Context()
    requester = context.socket(zmq.REQ)
    requester.connect("tcp://localhost:5555")

    while True:
        message = input("Enter your request: ")
        requester.send_string(message)

        # 等待应答
        response = requester.recv_string()
        print(f"Received response: {response}")

if __name__ == "__main__":
  create()

