# coding=utf-8

import wexpect
import threading
import queue
import time
import datetime
from util import *
           

class ADBManager:
    def __init__(self, config):
        self.config = config
        self.adb = './adb/adb.exe'
        self.device = config['adb_device']
        pipe = wexpect.spawn(self.adb + ' ' + config['adb_init_cmd'])
        pipe.expect(['connected', wexpect.EOF])
        # 链接shell
        self.shell_pipe = wexpect.spawn(self.adb + ' shell')
        
        self.key_status = {'1': 0, '10': 0}
        # print(self.key_status)
        # 后台shell
        self.shell_queue = queue.Queue()
        # self.cmd_list = []
        # 任务管理
        self.new_cmd = threading.Event()
        self.shell_thre = threading.Thread(target=self._adb_send_loop)
        self.shell_thre.start()
        self.current_key = '1'
        self.current_updown = '-1' # -1无定义 0UP 1DOWN
        


    def stop_loop(self):
        self.release_all_keys()
        self._adb_send_cmd(['exit'])
        self.shell_thre.join()

    def release_all_keys(self):
        for i in self.key_status:
            self.send_release_event(code=i)
    
    def _adb_send_loop(self):
        while True:
            self.new_cmd.wait()
            # check
            cmds = []
            while not self.shell_queue.empty():
                cmds.append(self.shell_queue.get())
            self.new_cmd.clear()    
            self.shell_pipe.sendline('\n'.join(cmds))
            if 'exit' in cmds:
                break
            
        # print('loop_done')
    
    def _adb_send_cmd(self, cmd):
        self.shell_queue.put(' '.join(cmd))
        self.new_cmd.set()
        
        # print(self.shell_pipe.readline())
    
    def _adb_send_event(self, param):
        self._adb_send_cmd(['sendevent', self.device] + param)
        
    def _send_syn_event(self):
        self._adb_send_event(['0', '0', '0'])

    def _send_update_ptr(self, code):
        if self.current_key != code:
            self._adb_send_event(['3', '47', code]) # ABS_MT_SLOT
            self.current_key = code
            
    def _send_update_updown(self, is_up): 
        if (is_up and self.current_updown != '0') or (not is_up and self.current_updown != '1'):
            self.current_updown = '0' if is_up else '1'
            self._adb_send_event(['1', '330', self.current_updown])
        
    def _send_touch_event(self, code, is_up, xy=None):
        # check status:
        if self.key_status[code] == 0 ^ is_up:
            # print(("up" if is_up else "down") + code)
            # step1 update current device ptr  ABS_MT_SLOT
            self._send_update_ptr(code)
            # step2 flash current code id      ABS_MT_TRACKING_ID
            self._adb_send_event(['3', '57', '-1' if is_up else self.current_key])
            # step 2.5 if there is xy
            if xy:
                self._send_position_event(xy[0], xy[1])
            # step3 up/down
            self._send_update_updown(is_up)
            # step4 sync
            self._send_syn_event()
            # fresh state
            self.key_status[code] = 0 if is_up else 1
        
    def send_release_event(self, xy=None, code='1'):
        self._send_touch_event(code, True, xy=xy)

    def send_press_event(self, xy=None, code='1'):
        # if xy is None: then repeat the last position
        self._send_touch_event(code, False, xy=xy)

    def _send_position_event(self, x, y):
        self._adb_send_event(['3', '53', str(x)])
        self._adb_send_event(['3', '54', str(y)])
        
    def send_tap_event(self, xy, duration=0,  code='1'):
        self.send_press_event(xy=xy, code=code)
        if duration > 0:
            time.sleep(duration)
        self.send_release_event()
    
    def send_move_event(self):
        pass
        # this is a demo showing how to drag:
        # press_event
        # then _send_position_event + _send_syn_event()
        # finally release
        # use adb shell getevent -l to monitor events!
        
    def parse_action(self, action):
        code = '10' # 增加了一个虚拟按钮
        def cvt_corr(xy):
            if not isinstance(xy, tuple):
                return None
            if len(xy) != 2:
                return None
            x, y = xy
            return (int(x * self.config["adb_shape"][0]), int(y * self.config["adb_shape"][1]))

        if 'tap' in action:
            self.send_tap_event(cvt_corr(action['tap']), code="1")
            
        elif 'release' in action:
            self.send_release_event(cvt_corr(action['release']), code=code)
            
        elif 'press' in action:
            self.send_press_event(cvt_corr(action['press']), code=code)
        
       
if __name__ == '__main__':
    cfg = load_cfg()
    f = ADBManager(cfg)
    f.send_tap_event(300, 200, duration=5)
    time.sleep(1)
    f.stop_loop()