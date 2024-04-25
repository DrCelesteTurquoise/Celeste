import tkinter as tk
import zmq
import threading

def send_message():
    topic = topic_entry.get()
    command = cmd_entry.get()
    message = f"{topic} {command}"
    socket.send_string(message)

def display_response(response):
    response_text.config(state=tk.NORMAL)
    response_text.insert(tk.END, response + "\n")
    response_text.config(state=tk.DISABLED)

def receive_responses():
    while True:
        response = client_socket.recv_string()
        display_response(response)

# ZeroMQ setup
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

# Tkinter setup
root = tk.Tk()
root.title("Server")

topic_label = tk.Label(root, text="Topic:")
topic_label.grid(row=0, column=0, padx=5, pady=5)

topic_entry = tk.Entry(root)
topic_entry.grid(row=0, column=1, padx=5, pady=5)

cmd_label = tk.Label(root, text="Command:")
cmd_label.grid(row=1, column=0, padx=5, pady=5)

cmd_entry = tk.Entry(root)
cmd_entry.grid(row=1, column=1, padx=5, pady=5)

send_button = tk.Button(root, text="Send", command=send_message)
send_button.grid(row=2, columnspan=2, padx=5, pady=5)

response_label = tk.Label(root, text="Client Response:")
response_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

response_text = tk.Text(root, height=5, width=50)
response_text.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
response_text.config(state=tk.DISABLED)

# ZeroMQ for receiving client responses
client_context = zmq.Context()
client_socket = client_context.socket(zmq.SUB)
# client_socket.bind("tcp://*:5556")
client_socket.connect("tcp://localhost:5556")
client_socket.setsockopt_string(zmq.SUBSCRIBE, "")

# Start a thread for receiving client responses
response_thread = threading.Thread(target=receive_responses, daemon=True)
response_thread.start()

root.mainloop()
