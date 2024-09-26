# SDL in ANL Entity N9_1 package 1.0 by TDai

import robotics as ro
from robotics import procedure as proc
import loca
import rack_status
import time

ro.debug_on()
c9 = ro.system.init('controller')
coater = ro.system.init('coater')
Keithley = ro.system.init('IV')

probe_loc = {
        1: 10050,  # 1st device
        2: 11350,  # 2nd device
        3: 12350,  # 3rd device
        4: 13250,  # 4th device
        5: 14250,  # 5th device
        6: 14950,  # 6th device
    }


def home_robot():
    c9.home_robot()
    
def servo_off():
    c9.robot_servo(False)
    
def servo_on():
    c9.robot_servo(True)
    
def move():

    Num = 2
    c9.reset_elect_probe()
    # c9.home_robot()
    c9.move_axis('pin_outer', 16000, vel=8000, accel=8000)
    # input('Check the gate electrode')
    time.sleep(3)

    c9.move_axis('pin_inner', probe_loc[Num], vel=8000, accel=8000)
    c9.set_output('pin_inner', True)
    time.sleep(1)

    c9.set_output('pin_inner', False)
    time.sleep(1)
    
    c9.move_axis('pin_inner', 0, vel=8000, accel=8000)
    c9.move_axis('pin_outer', 0, vel=8000, accel=8000)

def measure():
    
    Keithley.reset()
    exp = ro.workflow.load('workflow_OECT.py')
    # exp.Keithley.reset()

    # input('press any key to continue')

    # --------------------------------
    ID = '9b07T1'
    # --------------------------------

    smp = ro.sample.loads(ID)

    smp['inputs']['electrical_characterization._echem_characterization'] = 1
    exp.electrical_characterization_measure(smp)
    # exp.data_postprocessing(smp)

    todo = smp.get('workflow_todo', [])

    for step_name in ['electrical_characterization_measure']: #, 'store_sample', 'data_postprocessing']:
        if step_name in smp['workflow_todo']:
            ix = todo.index(step_name)
            smp['workflow_todo'][ix] = f"# {step_name}"

    smp.save()

def self_healing_wf_future():
    c9.home_robot()


    
if __name__ == '__main__':
    move()
