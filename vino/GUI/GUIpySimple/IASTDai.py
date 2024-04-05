# SDL Control Panel TDai 0.0 Version

import PySimpleGUI as sg
import WorkFlowEditor
import sys

# Main Control Panel Window

def make_window(theme):

    sg.theme(theme)  # 'Lightgreen'
    layout = [[sg.Text('SDL Control Panel TDai', font='Calibri 23 italic bold underline')],
              [sg.Text('Available Features:', font='Calibri 18')],
              [sg.Text('Input 1:', font='Calibri 13 italic bold'),
               sg.Text('Communication test with the desired entity', font='Calibri 13')],
              [sg.Text('Input 2:', font='Calibri 13 italic bold'), sg.Text('Execute workflows', font='Calibri 13')],
              [sg.Text('Input 3:', font='Calibri 13 italic bold'), sg.Text('Close', font='Calibri 13')],
              [sg.Text('Enter your command', font='Calibri 13'), sg.InputText()],
              [sg.Button('GO'), sg.Button('Exit')]]
    window_main = sg.Window('IAS Control Panel', layout)
    return window_main


def main():

    window_main = make_window(sg.theme('Lightgreen'))
    while True:
        event, values = window_main.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            
            print('Exit')

            break

        if values[0] == '1':
            print('comm test')
            # sg.popup('Entities - IAS Control Panel', 'Number of current online KUKA：', len(glv.g_conn_pool),
            #          'Entities Addresses', glv.g_conn_poolAddr, icon=r'IMG\IAS.ico')

        elif values[0] == '2':
            print('perform workflow')
            WorkFlowEditor.workflow()
        
        elif values[0] == '3':
            sys.exit()

    window_main.close()


if __name__ == '__main__':
    main()








