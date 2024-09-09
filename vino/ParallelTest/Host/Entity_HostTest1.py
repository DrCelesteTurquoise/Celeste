import zmq
import time
import threading
import tkinter as tk
from tkinter import messagebox


def init_host():
    context = zmq.Context()

    # 创建发布者socket，用于向所有entity发布全局指令
    pub = context.socket(zmq.PUB)
    pub.bind('tcp://130.202.150.36:5558')

    # 创建推送者socket，用于向特定entity发送工作流任务
    push = context.socket(zmq.PUSH)
    push.bind('tcp://130.202.150.36:5557')

    return pub, push, context


def send_global_command(pub, command):
    """
    发送全局命令给所有entity，适用于广播类型的指令
    """
    pub.send_string(f"all {command}")
    print(f"Sent global command: {command}")
    messagebox.showinfo("Command Sent", f"Sent global command: {command}")


def send_task(push, entity_name, task):
    """
    向特定的entity发送具体任务
    """
    push.send_string(f"{entity_name} {task}")
    print(f"Sent task to {entity_name}: {task}")
    messagebox.showinfo("Task Sent", f"Sent task to {entity_name}: {task}")


def workflow(push, entities):
    """
    定义一个简单的工作流，将任务依次分发给不同的entity
    """
    workflow_steps = [
        {'entity': entities[0], 'task': 'Step 1: Initialize'},
        {'entity': entities[1], 'task': 'Step 2: Process Data'},
        {'entity': entities[2], 'task': 'Step 3: Finalize'}
    ]
    
    for step in workflow_steps:
        send_task(push, step['entity'], step['task'])
        time.sleep(3)  # 模拟任务的间隔时间


def multi_workflow(push, entities_list):
    """
    同时执行多个工作流，分别给不同的实体集合分发任务
    """
    workflows = [
        [
            {'entity': entities_list[0][0], 'task': 'Workflow1: Step 1'},
            {'entity': entities_list[0][1], 'task': 'Workflow1: Step 2'}
        ],
        [
            {'entity': entities_list[1][0], 'task': 'Workflow2: Step 1'},
            {'entity': entities_list[1][1], 'task': 'Workflow2: Step 2'}
        ]
    ]

    for workflow in workflows:
        for step in workflow:
            send_task(push, step['entity'], step['task'])
            time.sleep(2)


def start_workflow(push, entities):
    """
    在 GUI 中启动工作流
    """
    threading.Thread(target=workflow, args=(push, entities)).start()


def start_multi_workflow(push, entities_list):
    """
    在 GUI 中启动多工作流
    """
    threading.Thread(target=multi_workflow, args=(push, entities_list)).start()


def create_gui(pub, push, entities):
    """
    创建一个简单的 tkinter GUI 来发送命令和任务
    """
    window = tk.Tk()
    window.title("Host Control Panel TDai")
    window.geometry('400x300')

    # 标签
    lbl = tk.Label(window, text="Host Control Panel", font=("Arial Bold", 14))
    lbl.pack(pady=10)

    # 单工作流按钮
    workflow_btn = tk.Button(window, text="Start Workflow", command=lambda: start_workflow(push, entities))
    workflow_btn.pack(pady=10)

    # 多工作流按钮
    multi_workflow_btn = tk.Button(window, text="Start Multiple Workflows", command=lambda: start_multi_workflow(push, [['entity1', 'entity2'], ['entity3', 'entity4']]))
    multi_workflow_btn.pack(pady=10)

    # 退出按钮
    exit_btn = tk.Button(window, text="Send Exit Command", command=lambda: send_global_command(pub, 'Exit'))
    exit_btn.pack(pady=10)

    # 发送全局命令按钮
    start_global_btn = tk.Button(window, text="Send Start Command", command=lambda: send_global_command(pub, 'Start Workflow'))
    start_global_btn.pack(pady=10)

    # 启动 GUI
    window.mainloop()


if __name__ == '__main__':
    # 初始化 ZeroMQ host
    pub, push, context = init_host()

    # 定义实体
    entities = ['entity1', 'entity2', 'entity3']

    # 启动 GUI 界面
    create_gui(pub, push, entities)

    # 关闭上下文
    context.term()
