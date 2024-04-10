import PySimpleGUI as sg
from threading import Thread
import sys
import socket
import zmq
import glv
import time


def configuration():

    sg.theme('Lightgreen')
    layout_configuration = [
        [sg.Text('ANL SDL Control Panel', font='Calibri 23 italic bold underline')],
        [sg.Text('Please finish the Host Configuration:', font='Calibri 18')],
        [sg.Text('Host IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56666)],
        [sg.Button('GO'), sg.Button('Exit')]]
    window_configuration = sg.Window('SDL Control Panel Launcher', layout_configuration)

    while True:
        event, values = window_configuration.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            sys.exit()
        glv.host_ip = values[0]
        glv.host_port = int(values[1])

        break
    window_configuration.close()


def init():

    glv.context = zmq.Context()
    glv.g_host_pub = glv.context.socket(zmq.PUB)
    glv.g_host_pub.bind(f"tcp://{glv.host_ip}:{glv.host_port}")
    
    glv.g_host_sub = glv.context.socket(zmq.SUB)
    glv.g_host_sub.connect("tcp://192.168.12.246:56616")  # MiR
    glv.g_host_sub.connect("tcp://192.168.12.246:56626")  # UR5e
    glv.g_host_sub.connect("tcp://192.168.12.230:56636")  # ChemS
    glv.g_host_sub.connect("tcp://192.168.12.240:56646")  # KLA
    glv.g_host_sub.connect("tcp://192.168.12.200:56656")  # GPC
    #glv.g_host_sub.connect("tcp://192.168.12.250:56676")  # Unknown 1
    #glv.g_host_sub.connect("tcp://192.168.12.250:56686")  # Unknow 2
    glv.g_host_sub.setsockopt_string(zmq.SUBSCRIBE, '')

    # 4 Bat part
    # glv.g_socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # glv.g_socket_server.bind((glv.host_ip, glv.host_port))
    # glv.g_socket_server.listen(6)
    #glv.g_socket_server.settimeout(30)

    print('server initialization done')


def accept_kukabat():
    while True:
        kukabat, addr = glv.g_socket_server.accept()
        glv.g_conn_pool.append(kukabat)
        glv.g_conn_poolAddr.append(addr)

        # new added
        thread = Thread(target=kukabatinfo_request, args=(kukabat, addr))
        thread.setDaemon(True)
        thread.start()


def kukabatinfo_request(kukabat, addr):
    while True:
        # time.sleep(1*10*60)
        time.sleep(1)
        kukabat.sendall('BatteryRequest\r'.encode(encoding='utf8'))
        batinfo = kukabat.recv(1024).decode(encoding='utf8')
        print(batinfo)
        if len(batinfo) == 0:
            kukabat.close()
            glv.g_conn_pool.remove(kukabat)
            glv.g_conn_poolAddr.remove(addr)
            print('one kukabat offline')
            break

if __name__ == '__main__':
    configuration()