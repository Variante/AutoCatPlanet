# -*- coding:utf-8 -*-
import mss
from util import *
from tkinter import *
import tkinter.font as tkFont
from PIL import Image, ImageDraw, ImageFont, ImageTk
from itertools import combinations
import numpy as np
import cv2
from datetime import datetime
import threading
import random
import wexpect
import time
from FishingManager import *
from ADBManager import *


class GameManager:
    def __init__(self, config):
        # roc.set_boot_state()
        self.check_interval = 1 / config['check_fps']
        self.cfg = config
        self.img_dict = {}
        self.load_img()
        self.run = True
        
        self.src_img = None
        self.src_time = 0
        
        self.text = "加载中……"
        self.bbox = {"pt": []}
        self.repeat = 0
        if "repeat" in config:
            self.repeat = config["repeat"]
        self.pause_game = False
        self.thread = threading.Thread(target=GameManager.check_loop, args=(self,))
        self.thread.start()
        
        # game mode: 0 默认无检测
        self.mode = 0
        
    def check_loop(self):
        time.sleep(1)
        
        def get_patch(img, area):
            h, w = img.shape[:2]
            return img[int(h * area[1]): int(h * area[3]), int(w * area[0]): int(w * area[2])]
        
        while self.run:
            # fishing:
            # res = fm.check_circle(img)
                
            if self.pause_game:
                self.mode = 0
                continue
                
            if self.src_img is not None:
                src = self.src_img[...,2]
                text_list = []
                self.mode = 0
                for item in self.cfg['data']:
                    name = item['file']
                    tgt = self.img_dict[name]
                    thre = item['thre']
                    area = item['area']
                    if 'comment' in item:
                        name = item['comment']
                    
                    
                    tgt = get_patch(tgt, area)
                    src_c = cv2.resize(get_patch(src, area), (tgt.shape[1], tgt.shape[0]))
                    
                    # print(tgt.shape, src_c.shape)

                    res = cv2.matchTemplate(src_c, tgt, cv2.TM_CCOEFF_NORMED)
                    val = np.max(res)
                    
                    
                    # print("Check " + name, val, thre)
                    tmp_text = f"{name}: {val:.2f}({thre:.2f})"
                    
                    if 'count' in item:
                        tmp_text += f"[{item['count']}]"
                        if self.repeat == 0: # skip this action
                            text_list.append(tmp_text + ' X')
                            continue
                        repeat_dif = item['count']
                    else:
                        repeat_dif = 0

                    if val > thre:
                        # cv2.imshow(name, src_c)
                        # cv2.waitKey(10)
                        # print(name, "checked")
                        tmp_text += " √"
                        self.mode = item['mode']
                        
                    text_list.append(tmp_text)
                    
                self.text = '\n'.join(text_list)
                
            else:
                self.mode = 0
                self.text = "Image Not Found"
                self.bbox["pt"] = []
                # print('-' * 9)
            time.sleep(self.check_interval)
            
        
    def load_img(self):
        self.img_dict = {}
        for item in self.cfg['data']:
            name = item['file']
            img = cv2.imread('./img/' + name, 0)
            w = self.cfg['match_width']
            h = int(w * img.shape[0] / img.shape[1])
            img = cv2.resize(img, (w, h))
            # print(img.shape)
            self.img_dict[name] = img
            
    def check_img(self, src, src_time):
        self.src_img = src
        self.src_time = src_time
        
    def set_config(self, cfg):
        self.cfg = cfg
        self.load_img()
        print("Config updated")
        
    def close(self):
        self.run = False
        self.thread.join()
            

def main(cfg):
    # Windows
    root = Tk()
    # Create a frame
    app = Frame(root)
    app.pack()

    # Create a label in the frame
    lmain = Label(app)
    lmain.pack()
    
    # ldtag1 = Label(app, font=tkFont.Font(size=15, weight=tkFont.BOLD))
    # ldtag1.pack()
    # lentry = Entry(app) 
    # lentry.pack()
    # ldtag = Label(app, font=tkFont.Font(size=15, weight=tkFont.BOLD))
    # ldtag.pack()
    ldres = Message(app, width=800, font=tkFont.Font(size=15, weight=tkFont.NORMAL))
    ldres.pack()
    
    root.title('AutoArk')
    # root.geometry('1300x760')
    target_name = cfg['name']
   
    scale = cfg['scale']

    save_img = False
    
    def onKeyPress(event):
        nonlocal save_img
        # print(event)
        if event.char in 'rR':
            cfg = load_cfg()
            gm.set_config(cfg)
        if event.char in 'sS':
            save_img = True

    def get_stick(des, win):
        words = des.split(',')
        value = 0
        for w in words:
            if w in ['top', 'left', 'width', 'height']:
                value += win[w]
            else:
                value += int(w)
        return value

    root.bind('<KeyPress>', onKeyPress)
    
    display_interval = int(1000 / cfg['display_fps'])
    
    last_mode = 0
    gm = GameManager(cfg)
    f = FishingManager(cfg)
    adb = ADBManager(cfg)

    with mss.mss() as m:
        def capture_stream():
            nonlocal save_img
            nonlocal last_mode

            win_info = get_window_roi(target_name, [0, 0, 1, 1], cfg['padding'])
            if win_info['left'] < 0 and win_info['top'] < 0:
                ldtag1.configure(text='未检测到窗口')
                ldtag.configure(text='')
                ldres.configure(text='')
                img_cache = None
            else:
                full_win = get_window_roi(target_name,[0, 0, 1, 1], [0, 0, 0, 0])
                if len(cfg['stick']) == 2:
                    root.geometry(f"+{get_stick(cfg['stick'][0], full_win)}+{get_stick(cfg['stick'][1], full_win)}")
                img = np.array(m.grab(win_info))[...,:3]
                img_time = time.perf_counter()
                pil_img = Image.fromarray(img[...,::-1])
                
                action = {}
                # detect game state
                gm.check_img(img, img_time)
                if last_mode != gm.mode:
                    f.clear()
                last_mode = gm.mode
                # check with Fishing manager
                if gm.mode in f.mode:
                    action = f.mode[gm.mode](img, img_time)
                    # pil_img = Image.fromarray(f.display)
                    
                adb.parse_action(action)
                
                """
                draw vis
                """
                # for pt in gm.bbox["pt"]:
                #     img = cv2.circle(img, pt, 5, (0, 0, 255), -1)

                # ldtag1.configure(text=gm.get_repeat())
                # ldtag.configure(text='')
                ldres.configure(text=gm.text)
                
                if save_img:
                    now = datetime.now()
                    date_time = now.strftime("./%H-%M-%S")
                    pil_img.save(date_time + ".png")
                    save_img = False
                
                if gm.mode == 0 and scale > 0:
                    pil_img = pil_img.resize((int(pil_img.size[0] * scale), int(pil_img.size[1] * scale)))
                else:
                    pil_img = Image.fromarray(f.display)
                
                
                # update the display
                imgtk = ImageTk.PhotoImage(image=pil_img)
                lmain.imgtk = imgtk
                lmain.configure(image=imgtk)
            lmain.after(display_interval, capture_stream) 

        capture_stream()
        root.mainloop()
    gm.close()
    adb.stop_loop()

def usage():
    print("AutoCatPlanet操作说明:\nS:保存当前截图\n需要手动开始、手动结算。" + '-'*8)


if __name__ == '__main__':
    usage()
    cfg = load_cfg()
    main(cfg)
