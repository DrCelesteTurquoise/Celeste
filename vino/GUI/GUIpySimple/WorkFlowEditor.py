import PySimpleGUI as sg
import glv
import time
import datetime
import csv
import pandas as pd
import os
import shutil
import json


def make_window():
    OnlineEdit_layout = [

        [sg.Text('Please edit your workflow in this tab')],

        [sg.InputText('Name: KUKA3; CMD: Position: LCMS, ChemS, SynLED, Home, ChargeS, WaitP4ChemS', size=(80, 1),
                      use_readonly_for_disable=True, disabled=True, key='-IN-')],
        [sg.InputText(
            'Name: KUKA3; CMD: Action: Charge, LcmsRacksInChemS, LcmsRacksInLcms, LcmsRacksOutChemS, LcmsRacksOutLcms',
            size=(80, 1), use_readonly_for_disable=True, disabled=True, key='-IN-')],
        [sg.InputText(
            'Name: KUKA3; CMD: Action: VialsInChemS, VialsInSynLED, VialsOutChemS, VialsOutSynLED, VialsHolderRefillSynLEDRE',
            size=(80, 1), use_readonly_for_disable=True, disabled=True, key='-IN-')],
        [sg.InputText('Name: LCMS; CMD: Action: InsertRack1,2; ExtractRack1,2; StartAnalysisRack1,2', size=(80, 1),
                      use_readonly_for_disable=True, disabled=True, key='-IN-')],
        [sg.InputText('Name: ChemSDoor; CMD: Action: Open, Close', size=(80, 1), use_readonly_for_disable=True,
                      disabled=True, key='-IN-')],
        [sg.InputText('Name: ChemS; CMD: Action: ExecuteDispensing, ExecuteReformat', size=(80, 1),
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
                        sg.Button('Upload'), sg.Button('Exit ')]]

    logging_layout = [[sg.Text("Your workflow progress will display here")],
                      [sg.Multiline(size=(60, 15), font='Courier 8', expand_x=True, expand_y=True, write_only=True,
                                    reroute_stdout=True, reroute_stderr=True, echo_stdout_stderr=True, autoscroll=True,
                                    auto_refresh=True)]
                      # [sg.Output(size=(60,15), font='Courier 8', expand_x=True, expand_y=True)]
                      ]

    layout_WF = [[sg.Text('Intelligent Automation System Control Panel', font='Calibri 23 italic bold underline')],
                 [sg.Text('Create your workflow online or Upload your predefined workflow:', font='Calibri 18')]]

    layout_WF += [[sg.TabGroup([[sg.Tab('Workflow Online Editor', OnlineEdit_layout),
                                 sg.Tab('Workflow Upload', UploadWF_layout),
                                 sg.Tab('Workflow Progress', logging_layout)
                                 ]], key='-TAB GROUP-', expand_x=True, expand_y=True), ],
                  [sg.Image(r'IMG\UoL.png', subsample=2), sg.Image(r'IMG\logoACL.png', subsample=2)]]

    window_WFNEW = sg.Window('Execute workflows - IAS Control Panel', layout_WF, icon=r'IMG\IAS.ico')

    return window_WFNEW


def workflow():
    window = make_window()

    # This is an Event Loop
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

                # add if condition here to check if send cmd to kuka4, if kuka4 then skip the first replys

                if name == 'KUKA4':
                    glv.g_host_pub.send_multipart([name.encode(), msg.encode()])
                    # kuka4hostsent = glv.g_host_sub.recv_string()
                    kuka4hostsent = glv.g_host_sub.recv_multipart()
                    received_message = b"".join(kuka4hostsent)
                    print('EntityKUKA4Host sent message:'+received_message.decode('utf-8'),
                          datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
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

                elif name == 'Host':
                    if msg == 'PauseToRefill':
                        refill = sg.popup_ok_cancel('Do you finish the refill work?', 'Press Ok to proceed',
                                                    'Press cancel to stop', title='OkCancel', icon=r'IMG\IAS.ico')
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
                                                         'Press cancel to stop', title='OkCancel', icon=r'IMG\IAS.ico')
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

        elif event == 'Upload':
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

                    if name == 'KUKA4':
                        glv.g_host_pub.send_multipart([name.encode(), msg.encode()])
                        kuka4hostsent = glv.g_host_sub.recv_multipart()
                        received_message = b"".join(kuka4hostsent)
                        print('EntityKUKA4Host sent message:' + received_message.decode('utf-8'),
                              datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y'), '\n')
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

                    elif name == 'Host':
                        if msg == 'PauseToRefill':
                            refill = sg.popup_ok_cancel('Do you finish the refill work?', 'Press Ok to proceed',
                                                        'Press cancel to stop', title='OkCancel', icon=r'IMG\IAS.ico')
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
                                                        'Press cancel to stop', title='OkCancel', icon=r'IMG\IAS.ico')
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
