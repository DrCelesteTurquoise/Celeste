import zmq
import time
import tkinter as tk
from tkinter import filedialog
import threading

class HostApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Host Control Panel")
        self.master.geometry("300x200")

        # 主窗口：提供两个功能按钮
        self.label = tk.Label(self.master, text="Select a Function", font=("Arial", 14))
        self.label.pack(pady=10)

        self.single_command_button = tk.Button(self.master, text="Send Command to Specific Entity", command=self.open_single_command_window)
        self.single_command_button.pack(pady=10)

        self.batch_command_button = tk.Button(self.master, text="Batch Command from File", command=self.open_batch_command_window)
        self.batch_command_button.pack(pady=10)

        # 初始化 ZMQ PUB-SUB sockets
        self.context = zmq.Context()
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind('tcp://*:5558')  # 用于发送指令

        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect('tcp://172.31.1.16:5553')  # 用于订阅所有 entity 的状态
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")  # 订阅所有消息

        self.entity_states = {}  # 存储每个 entity 的状态

        # 启动接收实体状态更新的线程
        self.state_thread = threading.Thread(target=self.receive_entity_states)
        self.state_thread.start()

    # 单独发送指令窗口
    def open_single_command_window(self):
        single_command_window = tk.Toplevel(self.master)
        single_command_window.title("Send Command to Specific Entity")
        single_command_window.geometry("400x200")

        tk.Label(single_command_window, text="Enter Command (Format: entity;command):").pack(pady=5)
        entity_entry = tk.Entry(single_command_window, width=40)
        entity_entry.pack(pady=5)

        def send_specific_command():
            user_input = entity_entry.get()
            if ';' in user_input:
                entity, cmd = user_input.split(';', 1)
                entity = entity.strip()
                cmd = cmd.strip()

                # 检查 entity 状态
                if self.entity_states.get(entity, 'Ready') == 'Ready':
                    # 发送指令
                    self.pub_socket.send_multipart([entity.encode(), cmd.encode()])
                    output_text.insert(tk.END, f"Sent command to {entity}: {cmd}\n")
                    output_text.see(tk.END)
                else:
                    output_text.insert(tk.END, f"{entity} is not ready. Current state: {self.entity_states.get(entity, 'Unknown')}\n")
                    output_text.see(tk.END)
            else:
                output_text.insert(tk.END, "Invalid input. Use format: entity;command\n")
                output_text.see(tk.END)

        send_button = tk.Button(single_command_window, text="Send Command", command=send_specific_command)
        send_button.pack(pady=5)

        output_text = tk.Text(single_command_window, height=5, width=50)
        output_text.pack(pady=10)

    # 批量命令窗口
    def open_batch_command_window(self):
        batch_command_window = tk.Toplevel(self.master)
        batch_command_window.title("Batch Command from File")
        batch_command_window.geometry("400x300")

        output_text = tk.Text(batch_command_window, height=10, width=50)
        output_text.pack(pady=10)

        def open_file():
            file_path = filedialog.askopenfilename(title="Select Command File", filetypes=(("Text Files", "*.txt"),))
            if file_path:
                with open(file_path, 'r') as file:
                    commands = [line.strip().split(';') for line in file.readlines()]
                output_text.insert(tk.END, f"Loaded {len(commands)} commands from {file_path}\n")

                start_button.config(state=tk.NORMAL)

                def batch_send():
                    for entity, cmd in commands:
                        # 等待 entity 状态变为 Ready
                        while self.entity_states.get(entity, 'Ready') != 'Ready':
                            output_text.insert(tk.END, f"{entity} is working. Waiting...\n")
                            output_text.see(tk.END)
                            time.sleep(60)  # 等待 1 分钟再检查

                        # 发送指令给 entity
                        self.pub_socket.send_multipart([entity.encode(), cmd.encode()])
                        output_text.insert(tk.END, f"Broadcasted to {entity}: {cmd}\n")
                        output_text.see(tk.END)
                        time.sleep(1)  # 模拟广播频率

                    output_text.insert(tk.END, "Batch broadcasting completed.\n")
                    start_button.config(state=tk.DISABLED)

                start_button = tk.Button(batch_command_window, text="Start Broadcasting", state=tk.DISABLED, command=batch_send)
                start_button.pack(pady=5)

        open_button = tk.Button(batch_command_window, text="Open Command File", command=open_file)
        open_button.pack(pady=5)

    # 监听并接收所有 entity 的状态更新
    def receive_entity_states(self):
        while True:
            try:
                entity, state = self.sub_socket.recv_multipart()
                entity = entity.decode()
                state = state.decode()
                self.entity_states[entity] = state  # 更新 entity 的状态
                print(f"Received {entity} state: {state}")  # 输出到控制台便于调试
            except zmq.ZMQError as e:
                print(f"Error receiving entity state: {e}")
                break

    def on_closing(self):
        self.pub_socket.close()
        self.sub_socket.close()
        self.context.term()
        self.master.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = HostApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
