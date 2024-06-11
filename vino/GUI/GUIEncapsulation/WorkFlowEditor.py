import PySimpleGUI as sg
import glv
import time
import datetime

import shutil
import os



def make_window(theme):
    
    sg.theme(theme)
    OnlineEdit_layout = [

        [sg.Text('Please edit your workflow in this tab')],

        [sg.InputText('Name: MiR250; CMD: Position: ChemSpeed, KLA, GPC, N9, Charger', size=(80, 1),
                      use_readonly_for_disable=True, disabled=True, key='-IN-')],
        [sg.InputText(
            'Name: UR5e; CMD: Action: ToolChangeDemo, B',
            size=(80, 1), use_readonly_for_disable=True, disabled=True, key='-IN-')],
        [sg.InputText(
            'Name: N9; CMD: Action: A, B',
            size=(80, 1), use_readonly_for_disable=True, disabled=True, key='-IN-')],
        [sg.InputText(
            'Name: Tecan; CMD: Action: A, B',
            size=(80, 1), use_readonly_for_disable=True, disabled=True, key='-IN-')],
        [sg.InputText('Name: KLA; CMD: Action: A, B, C', size=(80, 1),
                      use_readonly_for_disable=True, disabled=True, key='-IN-')],
        [sg.InputText('Name: ChemSpeed; CMD: Action: SimDemo, CapDemo', size=(80, 1), use_readonly_for_disable=True,
                      disabled=True, key='-IN-')],
        [sg.InputText('Name: GPC; CMD: Action: A, B', size=(80, 1),
                      use_readonly_for_disable=True, disabled=True, key='-IN-')],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Text('Name:', font='Calibri 8 italic bold'), sg.InputText()],
        [sg.Text('CMD:', font='Calibri 8 italic bold'), sg.InputText()],

        [sg.Button('Online_Edit_Done'), sg.Button('Exit')]]

    UploadWF_layout = [[sg.T('Please upload your predefined workflow in this tab')],
                       [sg.ProgressBar(100, orientation='h', size=(20, 20), key='-PROGRESS BAR-'),
                        sg.Button('Upload_WF'), sg.Button('Exit ')]]
    
    Upload_ChemS_Config_layout = [[sg.T('Please upload your predefined configuration file to ChemSpeed in this tab')],
                       [sg.ProgressBar(100, orientation='h', size=(20, 20), key='-PROGRESS BAR-'),
                        sg.Button('Upload_to_ChemSpeed'), sg.Button('Exit ')]]
    
    Upload_N9_1_Config_layout = [[sg.T('Please upload your predefined configuration file to N9_1 in this tab')],
                       [sg.ProgressBar(100, orientation='h', size=(20, 20), key='-PROGRESS BAR-'),
                        sg.Button('Upload_to_N9_1'), sg.Button('Exit ')]]
    
    Upload_N9_2_Config_layout = [[sg.T('Please upload your predefined configuration file to N9_2 in this tab')],
                       [sg.ProgressBar(100, orientation='h', size=(20, 20), key='-PROGRESS BAR-'),
                        sg.Button('Upload_to_N9_2'), sg.Button('Exit ')]]

    logging_layout = [[sg.Text("Your workflow progress will display here")],
                      [sg.Multiline(size=(60, 15), font='Courier 8', expand_x=True, expand_y=True, write_only=True,
                                    reroute_stdout=True, reroute_stderr=True, echo_stdout_stderr=True, autoscroll=True,
                                    auto_refresh=True)]
                      # [sg.Output(size=(60,15), font='Courier 8', expand_x=True, expand_y=True)]
                      ]

    layout_WF = [[sg.Text('ANL SDL Control Panel', font='Calibri 23 italic bold underline')],
                 [sg.Text('Create your workflow online or Upload your predefined workflow:', font='Calibri 18')]]

    layout_WF += [[sg.TabGroup([[sg.Tab('Workflow Online Editor', OnlineEdit_layout),
                                 sg.Tab('Upload Config file to ChemSpeed', Upload_ChemS_Config_layout),
                                 sg.Tab('Upload Config file to N9_1', Upload_N9_1_Config_layout),
                                 sg.Tab('Upload Config file to N9_2', Upload_N9_2_Config_layout),
                                 sg.Tab('Workflow Upload', UploadWF_layout),
                                 sg.Tab('Workflow Progress', logging_layout)
                                 ]], key='-TAB GROUP-', expand_x=True, expand_y=True), ]]

    window_WFNEW = sg.Window('Execute workflows - SDL Control Panel - TDai', layout_WF, icon=r'C:\NFTT\BTC\Test\VINODDD\Main\IMG\tree.ico')

    return window_WFNEW


def workflow():
    window = make_window(sg.theme('Lightgreen'))

    while True:
        event, values = window.read(timeout=100)
        if event == "Exit" or event == 'Exit ' or event == sg.WIN_CLOSED:
            break
        elif event == 'Online_Edit_Done':
            i = 0
            while True:
                name = values[i]
                if len(name) == 0:
                    time.sleep(1)
                    break
                msg = values[i + 1]
 
                if name == 'Host':
                    if msg == 'PauseToRefill':
                        refill = sg.popup_ok_cancel('Do you finish the refill work?', 'Press Ok to proceed',
                                                    'Press cancel to stop', title='OkCancel')
                        if refill == 'OK':

                            print('Refill work done and continue',
                                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                            i += 2
                        elif refill == 'Cancel':

                            print('Refill work not finished has to stop, stop in 3 sec',
                                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                            time.sleep(3)
                            break

                    elif msg == 'SafetyCheck':
                        safetycheck = sg.popup_ok_cancel('Do you finish the safety check work?', 'Press Ok to proceed',
                                                         'Press cancel to stop', title='OkCancel')
                        if safetycheck == 'OK':

                            print('Safety check work done and continue',
                                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                            i += 2
                        elif safetycheck == 'Cancel':

                            print('Safety issues found, stop in 3 sec',
                                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                            time.sleep(3)
                            break

                    elif msg == 'Wait':
                        # time.sleep(2*60*60)
                        print('Host Wait now',
                              datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                        time.sleep(3)
                        print('Host Wait Finished',
                              datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                        i += 2
                    else:
                        print('CMD for Host incorrect, will exit',
                              datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                        break

                else:
                    glv.g_host_pub.send_multipart([name.encode(), msg.encode()])
                    feedback = glv.g_host_sub.recv_string()
                    if 'Completed' in feedback:
                        time.sleep(1)
                        print(feedback,
                              datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                        i += 2
                    else:
                        time.sleep(1)
                        print(feedback,
                              datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                        break
        
        elif event == 'Upload_to_ChemSpeed':
            print('Going to upload the predefined Config to ChemSpeed!',
                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
            Predefined_Config = sg.popup_get_file('Choose your file', keep_on_top=True)
            sg.popup("You chose: " + str(Predefined_Config), keep_on_top=True)
            
            source_file = Predefined_Config
            dest_path = r"\\192.168.12.230\Users\Operator\Desktop\AutoWF\files"
            shutil.copy(source_file, dest_path)
            
        elif event == 'Upload_to_N9_1':
            print('Going to upload the predefined Config to N9_1!',
                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
            Predefined_Config = sg.popup_get_file('Choose your file', keep_on_top=True)
            sg.popup("You chose: " + str(Predefined_Config), keep_on_top=True)
            
            source_file = Predefined_Config
            dest_path = r"C:\path\to\your\file.txt"
            shutil.copy(source_file, dest_path)
            
        elif event == 'Upload_to_N9_2':
            print('Going to upload the predefined Config to N9_2!',
                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
            Predefined_Config = sg.popup_get_file('Choose your file', keep_on_top=True)
            sg.popup("You chose: " + str(Predefined_Config), keep_on_top=True)
            
            source_file = Predefined_Config
            dest_path = r"C:\path\to\your\file.txt"
            shutil.copy(source_file, dest_path)
        
        elif event == 'Upload_WF':
            print('Going to upload the predefined workflow!',
                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
            Predefined_WF = sg.popup_get_file('Choose your file', keep_on_top=True)
            sg.popup("You chose: " + str(Predefined_WF), keep_on_top=True)

            with open(Predefined_WF, 'r') as file:
                for line in file:
                    parts = line.split(';')
                    if len(parts) >= 2:
                        name = parts[0]
                        msg = parts[1].rstrip("\n")
                    else:
                        print('CMD error',
                              datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                        break

                    if name == 'Host':
                        if msg == 'PauseToRefill':
                            refill = sg.popup_ok_cancel('Do you finish the refill work?', 'Press Ok to proceed',
                                                        'Press cancel to stop', title='OkCancel')
                            if refill == 'OK':

                                print('Refill work done and continue',
                                      datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                            elif refill == 'Cancel':

                                print('Refill work not finished has to stop, stop in 3 sec',
                                      datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                                time.sleep(3)
                                break

                        elif msg == 'SafetyCheck':
                            safetycheck = sg.popup_ok_cancel('Do you finish the safety check work?', 'Press Ok to proceed',
                                                        'Press cancel to stop', title='OkCancel')
                            if safetycheck == 'OK':

                                print('Safety check work done and continue',
                                      datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                            elif safetycheck == 'Cancel':

                                print('Safety issues found, stop in 3 sec',
                                      datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                                time.sleep(3)
                                break

                        elif msg == 'Wait':
                            # time.sleep(2*60*60)
                            print('Host Wait now',
                                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                            time.sleep(3)
                            print('Host Wait Finished',
                                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                        else:
                            print('CMD for Host incorrect, will exit',
                                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                            break

                    else:
                        glv.g_host_pub.send_multipart([name.encode(), msg.encode()])
                        feedback = glv.g_host_sub.recv_string()
                        if 'Completed' in feedback:
                            time.sleep(1)
                            print(feedback,
                                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                        else:
                            time.sleep(1)
                            print(feedback,
                                  datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
                            break

        elif event == 'Test Progress bar':
            print("[LOG] Clicked Test Progress Bar!")
            progress_bar = window['-PROGRESS BAR-']
            for i in range(100):
                print("[LOG] Updating progress bar by 1 step (" + str(i) + ")")
                progress_bar.update(current_count=i + 1)
            print("[LOG] Progress bar complete!")

    window.close()
