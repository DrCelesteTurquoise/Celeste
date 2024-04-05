import PySimpleGUI as sg
import glv
import zmq


def communication():
    layout_Smsg = [
        [sg.Text('Intelligent Automation System Control Panel', font='Calibri 23 italic bold underline')],
        [sg.Text('Communication test with the desired entity', font='Calibri 18')],
        [sg.Text('Please enter the info:', font='Calibri 13 italic bold'),
         sg.Text("the name of desired entity, your CMD", font='Calibri 13')],
        [sg.Text('Name:', font='Calibri 13 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 13 italic bold'), sg.InputText()],
        [sg.Button('OK'), sg.Button('Exit')],
        [sg.Image(r'IMG\UoL.png', subsample=2), sg.Image(r'IMG\logoACL.png', subsample=2)]]
    # [sg.Column([[sg.Image(r'UoL.png')]], justification='center')]]
    window_Smsg = sg.Window('Communication Test - IAS Control Panel', layout_Smsg, icon=r'IMG\IAS.ico')
    while True:
        event, values = window_Smsg.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        topic = values[0]
        msg = values[1]

        glv.g_host_pub.send_multipart([topic.encode(), msg.encode()])

        feedback = glv.g_host_sub.recv_string()
        sg.Popup('Entity:', topic, 'Message received:', feedback, icon=r'IMG\IAS.ico')  # , means newline
    window_Smsg.close()