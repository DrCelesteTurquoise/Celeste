import PySimpleGUI as sg
import glv



def communication():
    
    sg.theme('Lightgreen')
    layout_Smsg = [
        [sg.Text('ANL SDL Control Panel', font='Calibri 23 italic bold underline')],
        [sg.Text('Communication test with the desired entity', font='Calibri 18')],
        [sg.Text('Please enter the info:', font='Calibri 13 italic bold'),
         sg.Text("the name of desired entity, your CMD", font='Calibri 13')],
        [sg.Text('Name:', font='Calibri 13 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 13 italic bold'), sg.InputText()],
        [sg.Button('OK'), sg.Button('Exit')]]
    
    window_Smsg = sg.Window('Communication Test - SDL Control Panel', layout_Smsg)
    while True:
        event, values = window_Smsg.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        topic = values[0]
        msg = values[1]

        glv.g_host_pub.send_multipart([topic.encode(), msg.encode()])

        feedback = glv.g_host_sub.recv_string()
        sg.Popup('Entity:', topic, 'Message received:', feedback)
    window_Smsg.close()
    
if __name__ == '__main__':
    communication()