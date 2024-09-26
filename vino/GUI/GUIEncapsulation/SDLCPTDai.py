# SDL Control Panel TDai 0.0 Version

import PySimpleGUI as sg
import WorkFlowEditor
import CommTestW
import ConfigW
import glv
import sys



def make_window(theme):

    sg.theme(theme)  # 'Lightgreen'
    layout = [[sg.Text('ANL SDL Main Control Panel - TDai', font='Calibri 23 italic bold underline')],
              [sg.Text('Available Features:', font='Calibri 18')],
              [sg.Text('Input 1:', font='Calibri 13 italic bold'),
               sg.Text('Communication test with the desired entity', font='Calibri 13')],
              [sg.Text('Input 2:', font='Calibri 13 italic bold'), sg.Text('Execute workflows', font='Calibri 13')],
              [sg.Text('Input 3:', font='Calibri 13 italic bold'), sg.Text('Close', font='Calibri 13')],
              [sg.Text('Enter your command', font='Calibri 13'), sg.InputText()],
              [sg.Button('GO'), sg.Button('Exit')]]
    window_main = sg.Window('Main Control Panel - TDai', layout, resizable=True, icon=r'C:\NFTT\BTC\Test\VINODDD\Main\IMG\tree.ico')
    return window_main


def main():

    window_main = make_window(sg.theme('Lightgreen'))
    while True:
        event, values = window_main.read()
        if event == sg.WIN_CLOSED or event == 'Exit':          
            glv.g_host_pub.close()
            glv.g_host_sub.close()
            glv.context.term()

            break

        if values[0] == '1':
            CommTestW.communication()

        elif values[0] == '2':
            WorkFlowEditor.workflow()
        
        elif values[0] == '3':
            sys.exit()

    window_main.close()


if __name__ == '__main__':
    ConfigW.configuration()
    ConfigW.init()
    main()








