import tkinter as tk
import zmq
import threading

class QServer:
    def __init__(self, root):
        self.root = root
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:5555")
        
        self.client_context = zmq.Context()
        self.client_socket = self.client_context.socket(zmq.SUB)
        self.client_socket.connect("tcp://localhost:5556")
        self.client_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        
        self.create_gui()
        self.start_receive_thread()

    def create_gui(self):
        self.topic_label = tk.Label(self.root, text="Topic:")
        self.topic_label.grid(row=0, column=0, padx=5, pady=5)

        self.topic_entry = tk.Entry(self.root)
        self.topic_entry.grid(row=0, column=1, padx=5, pady=5)

        self.cmd_label = tk.Label(self.root, text="Command:")
        self.cmd_label.grid(row=1, column=0, padx=5, pady=5)

        self.cmd_entry = tk.Entry(self.root)
        self.cmd_entry.grid(row=1, column=1, padx=5, pady=5)

        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.send_button.grid(row=2, columnspan=2, padx=5, pady=5)

        self.response_label = tk.Label(self.root, text="Client Response:")
        self.response_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        self.response_text = tk.Text(self.root, height=5, width=50)
        self.response_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        self.response_text.config(state=tk.DISABLED)

    def send_message(self):
        topic = self.topic_entry.get()
        command = self.cmd_entry.get()
        message = f"{topic} {command}"
        self.socket.send_string(message)

    def display_response(self, response):
        self.response_text.config(state=tk.NORMAL)
        self.response_text.insert(tk.END, response + "\n")
        self.response_text.config(state=tk.DISABLED)

    def receive_responses(self):
        while True:
            response = self.client_socket.recv_string()
            self.display_response(response)

    def start_receive_thread(self):
        response_thread = threading.Thread(target=self.receive_responses, daemon=True)
        response_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Server")
    server = QServer(root)
    root.mainloop()
