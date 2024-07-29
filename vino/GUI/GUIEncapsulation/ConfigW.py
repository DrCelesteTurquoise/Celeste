import PySimpleGUI as sg
import sys
import zmq
import glv


def configuration():

    sg.theme('Lightgreen')
    layout_configuration = [
        [sg.Text('ANL SDL Main Control Panel Configuration - TDai', font='Calibri 23 italic bold underline')],
        [sg.Text('Please finish the Configuration:', font='Calibri 18')],
        [sg.Text('Host IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('Host Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56666)],
        
        [sg.Text('MiR250 IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('MiR250 Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56616)],
        
        [sg.Text('UR5e IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('UR5e Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56626)],
        
        [sg.Text('ChemSpeed IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.230')],
        [sg.Text('ChemSpeed Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56636)],
        
        [sg.Text('KLA IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('KLA Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56646)],
        
        [sg.Text('GPC IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('GPC Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56656)],
        
        [sg.Text('Tecan IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('Tecan Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56676)],
        
        [sg.Text('N92 IP', font='Calibri 13 italic bold'), sg.InputText(default_text='192.168.12.246')],
        [sg.Text('N92 Port Number', font='Calibri 13 italic bold'), sg.InputText(default_text=56686)],
        
        [sg.Button('OK&GO'), sg.Button('Exit')]]
    window_configuration = sg.Window('Control Panel Configuration Launcher - TDai', layout_configuration, icon=r'C:\NFTT\BTC\Test\VINODDD\Main\IMG\tree.ico')
    

    while True:
        event, values = window_configuration.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            sys.exit()
        glv.host_ip = values[0]
        glv.host_port = int(values[1])
        
        glv.mir250_ip = values[2]
        glv.mir250_port = int(values[3])
        
        glv.ur5e_ip = values[4]
        glv.ur5e_port = int(values[5])
        
        glv.chemspeed_ip = values[6]
        glv.chemspeed_port = int(values[7])
        
        glv.kla_ip = values[8]
        glv.kla_port = int(values[9])
        
        glv.gpc_ip = values[10]
        glv.gpc_port = int(values[11])
        
        glv.tecan_ip = values[12]
        glv.tecan_port = int(values[13])
        
        glv.N92_ip = values[14]
        glv.N92_port = int(values[15])

        break
    window_configuration.close()


def init():

    glv.context = zmq.Context()
    glv.g_host_pub = glv.context.socket(zmq.PUB)
    glv.g_host_pub.bind(f"tcp://{glv.host_ip}:{glv.host_port}")
    
    glv.g_host_sub = glv.context.socket(zmq.SUB)
    glv.g_host_sub.connect(f"tcp://{glv.mir250_ip}:{glv.mir250_port}")
    glv.g_host_sub.connect(f"tcp://{glv.ur5e_ip}:{glv.ur5e_port}")
    glv.g_host_sub.connect(f"tcp://{glv.chemspeed_ip}:{glv.chemspeed_port}")
    glv.g_host_sub.connect(f"tcp://{glv.kla_ip}:{glv.kla_port}")
    glv.g_host_sub.connect(f"tcp://{glv.gpc_ip}:{glv.gpc_port}")
    glv.g_host_sub.connect(f"tcp://{glv.tecan_ip}:{glv.tecan_port}")
    glv.g_host_sub.connect(f"tcp://{glv.N92_ip}:{glv.N92_port}")
    
    glv.g_host_sub.setsockopt_string(zmq.SUBSCRIBE, '')

    print('server initialization done')
    

if __name__ == '__main__':
    configuration()
    init()