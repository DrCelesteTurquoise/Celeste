from north import NorthC9
import locations
import time
import cv2
import os

c9 = NorthC9('A', network_serial='AU06EWYQ')


def home_robot():
    c9.home_robot()
    
def servo_off():
    c9.robot_servo(False)
    
def servo_on():
    c9.robot_servo(True)
    

def snapshot(folder_path, interval_minutes, duration_hours):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print('Cannot enable the Camera')
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 4416)  # Set width to 1920 pixels
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1242)  # Set height to 1080 pixels

    interval_seconds = interval_minutes * 60
    total_duration_seconds = duration_hours * 60 * 60
    num_photos = total_duration_seconds // interval_seconds

    try:
        for i in range(num_photos):
            ret, frame = cap.read()
            if not ret:
                print(f'Cannot load pic {i+1}')
                break
            filename = os.path.join(folder_path, f'Photo_{i+1:03d}.jpg')
            cv2.imwrite(filename, frame)
            print(f'Saved:{filename}')
            time.sleep(interval_seconds)
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
def self_healing_wf():
    # c9.move_robot_cts(45,21362,34078,9660) #straightline
    c9.move_robot_cts(45,30265,40010,10363)
    # c9.move_robot_cts(*locations.fixed_modules_loc['blade']['pre_pos'])
    # c9.open_gripper
    # time.sleep(1)
    # c9.move_robot_cts(*locations.fixed_modules_loc['blade']['pos'])
    # time.sleep(1)
    # c9.close_gripper
    # time.sleep(1)
    # c9.move_robot_cts(*locations.fixed_modules_loc['blade']['pre_pos'])
    
    # need to go to the first wafer in move xy mode then run the loop to cut different samples
    
    # goto the 1th pos for the wafer:
    time.sleep(1)
    c9.move_robot_cts(265,31456,25005,12416)
    time.sleep(1)
    
    for wafer_pos in locations.selfhealing_wafers_loc.values():
        c9.move_xy(*wafer_pos['pre_pos'])
        time.sleep(1)
        c9.move_z(159.5)
        time.sleep(1)
        c9.move_z(168)
        time.sleep(1)
    
    c9.move_robot_cts(45,30265,40010,10363)
        

def self_healing_wf_future():
    c9.home_robot()
    c9.move_robot_cts(*locations.fixed_modules_loc['bernoulligripper']['pre_pos'])
    c9.open_gripper
    time.sleep(1)
    c9.move_robot_cts(*locations.fixed_modules_loc['bernoulligripper']['pos'])
    time.sleep(1)
    c9.close_gripper
    time.sleep(1)
    c9.move_robot_cts(*locations.fixed_modules_loc['bernoulligripper']['pre_pos'])
    
    
    # one loop for 24 times (sample preparation for cut):
    # 1th: transfer 1th sample to spin coater then pick up 1th tip to 1th vial
    # then to spin coating (details:) then wait for 15 mins then transfer back to 1th sample
    
    # Spin coating condition
    # Draw up 150µL of the reacted polymer.
    # While rotating at 100 rpm, dip the polymer onto the wafer.
    # After the dip, adjust the rotational speeds as follows: 100 rpm for 30 seconds, then 200 rpm for 30 seconds, and finally 300 rpm for 1 minute (totally 2 min).
    # Waiting for 1min.
    # Repeat the aforementioned steps once.
    # The spin coating process time for one sample is 5 mins.
        
    for wafer_pos, tip_pos, sample_pos in zip(locations.selfhealing_wafers_loc.values(), locations.tips_loc.values(), locations.selfhealing_samples_loc.values()):
        c9.move_robot_cts(*wafer_pos['pre_pos'])
        c9.move_robot_cts(*wafer_pos['pos'])
        c9.bernoulli_on()
        time.sleep(1)
        c9.move_robot_cts(*wafer_pos['pre_pos'])
        # lid up (air 3 is the lid)
        c9.set_output(3, True)
        c9.move_robot_cts(*locations.fixed_modules_loc['spincoater']['pre_pos'])
        c9.move_robot_cts(*locations.fixed_modules_loc['spincoater']['pos'])
        c9.bernoulli_off()
        # suck on (air 4 is the sucking)
        c9.set_output(4, True)
        c9.move_robot_cts(*locations.fixed_modules_loc['spincoater']['pre_pos'])
        # lid down (air 3 is the lid)
        c9.set_output(3, False)
        
        # liquid disp start:
        # put back gripper
        c9.move_robot_cts(*locations.fixed_modules_loc['bernoulligripper']['pre_pos'])
        c9.move_robot_cts(*locations.fixed_modules_loc['bernoulligripper']['pos'])
        c9.open_gripper
        c9.move_robot_cts(*locations.fixed_modules_loc['bernoulligripper']['pre_pos'])
        c9.move_robot_cts(*tip_pos['pre_pos'])
        
        
        


    
    # one loop for 24 times (cut samples):
    # 1th: pick up tool to cut 24 times
    
    # camera pic capture every 30 mins for 3 days
    
    # target self healing within one day
    
    # c9.move_robot_cts(*locations.prevacuumgripper_pos) # preVacuumGripper pos

    
if __name__ == '__main__':
    # print('cool')
    time.sleep(5)
    self_healing_wf()
    
    
    # snapshot
    # folder = 'captured_photos'
    # interval = 1  # every 1min
    # duration = 48   # last 48h
    # snapshot(folder, interval, duration)