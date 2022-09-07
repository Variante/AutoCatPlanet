# -*- coding:utf-8 -*-
import mss
from util import *
from tkinter import *
import tkinter.font as tkFont
from PIL import Image, ImageDraw, ImageFont, ImageTk
from itertools import combinations
import numpy as np
import cv2
import threading
import random
import time
from FishingManager import *
from GeneManager import *
from OCRManager import *
from ADBManager import *
from GraffitiManager import *
from datetime import datetime


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
        self.game_group = 0
        self.game_group_list = [
            '半自动钓鱼',
            '猫球基因预测',
            '自动涂鸦一本'
        ]
        
        for i, j in enumerate(self.game_group_list):
            print(f'数字{i + 1}: {j} ' + ('[默认]' if i == 0 else ''))
        print('=' * 8)
        
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
        
    def get_group(self):
        if self.game_group >= len(self.game_group_list) or self.game_group < 0:
            self.game_group = 0
        return self.game_group_list[self.game_group]
        
    def check_loop(self):
        time.sleep(1)
        
        while self.run:
            # fishing:
            # res = fm.check_circle(img)
                
            if self.pause_game:
                self.mode = 0
                self.text = '暂停'
                
            elif self.src_img is not None:
                text_list = []
                self.mode = 0
                for item in self.cfg['data']:
                    if 'group' not in item:
                        group = 0
                    else:
                        group = item['group']
                    if group != self.game_group:
                        continue
                    chn = item['chn']
                    src = self.src_img[...,chn]
                    name = item['file']
                    comment = item['comment']
                    tgt = self.img_dict[comment]
                    thre = item['thre']
                    area = item['area']
                    
                        
                    # print(src.shape, area)
                    src_c = get_patch(src, area)
                    # print(src.shape, tgt.shape)
                    tgt_c = cv2.resize(tgt, (src_c.shape[1], src_c.shape[0]))
                    
                    # cv2.imshow(comment, np.hstack([src_c, tgt_c]))
                    # cv2.waitKey(1)
                    res = cv2.matchTemplate(src_c, tgt_c, cv2.TM_CCOEFF_NORMED)
                    val = np.max(res)
                    
                    tmp_text = f"{comment}: {val:.2f}({thre:.2f})"
                    
                    if 'count' in item:
                        tmp_text += f"[{item['count']}]"
                        if self.repeat == 0: # skip this action
                            text_list.append(tmp_text + ' X')
                            continue
                        repeat_dif = item['count']
                    else:
                        repeat_dif = 0

                    if val > thre:
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
            comment = item['comment']
            chn = item['chn']
            img = cv2.imread('./img/' + name)[:, :, chn]
            w = self.cfg['match_width']
            h = int(w * img.shape[0] / img.shape[1])
            img = cv2.resize(img, (w, h))
            # print(img.shape)
            area = item['area']
            self.img_dict[comment] = get_patch(img, area)
            
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
    ldtag = Label(app, font=tkFont.Font(size=15, weight=tkFont.BOLD))
    ldtag.pack()
    ldres = Message(app, width=800, font=tkFont.Font(size=13, weight=tkFont.NORMAL))
    ldres.pack()
    
    root.title('AutoCatPlanet')
    # root.geometry('1300x760')
    target_name = cfg['name']
   
    scale = cfg['scale']

    save_img = False
    auto_padding = False
    do_test = False
    
    def onKeyPress(event):
        nonlocal save_img
        nonlocal auto_padding
        nonlocal do_test
        
        # print(event)
        if event.char in ' ':
            gm.pause_game = not gm.pause_game
        elif event.char in 'qQ':
            root.quit()
        # 采集猫球基因用
        # elif event.char in 'uio':
        #     do_test = event.char
        elif event.char in 'sS':
            save_img = True
        elif event.char in 'pP':
            auto_padding = True and cfg['autopadding']
        elif event.char in '123456789':
            gm.game_group = int(event.char) - 1

    def get_stick(des, win):
        words = des.split(',')
        value = 0
        for w in words:
            if w in ['top', 'left', 'width', 'height']:
                value += win[w]
            else:
                value += int(w)
        return value

    display_interval = int(1000 / cfg['display_fps'])
    
    last_mode = 0
    gm = GameManager(cfg)
    ocr = OCRManager()
    gene = GeneManager(cfg, ocr)
    f = FishingManager(cfg)
    adb = ADBManager(cfg)
    graff = GraffitiManager(cfg)
    
    root.bind('<KeyPress>', onKeyPress)
    
    with mss.mss() as m:
        def capture_stream():
            nonlocal save_img
            nonlocal last_mode
            nonlocal auto_padding
            nonlocal do_test

            win_info = get_window_roi(target_name, [0, 0, 1, 1], [0] * 4 if auto_padding else cfg['padding'])
            if win_info['left'] < 0 and win_info['top'] < 0:
                ldtag.configure(text='未检测到窗口')
                ldres.configure(text='')
                img_cache = None
            else:
                full_win = get_window_roi(target_name,[0, 0, 1, 1], [0, 0, 0, 0])
                if len(cfg['stick']) == 2:
                    root.geometry(f"+{get_stick(cfg['stick'][0], full_win)}+{get_stick(cfg['stick'][1], full_win)}") 
                img = np.array(m.grab(win_info))[...,:3]
                
                if auto_padding:
                    fake_gray = np.mean(img, axis=-1)
                    padx = np.median(fake_gray, axis=0)
                    pady = np.median(fake_gray, axis=1)
                    
                    def find_padding(src):
                        i = 0
                        j = src.shape[0] - 1
                        thre = cfg['autopadding_thre']
                        move = True
                        while i < j and move:
                            move = False
                            if src[i] < thre:
                                i += 1
                                move = True
                            if src[j] < thre:
                                j -= 1
                                move = True
                        return [i, src.shape[0] - j - 1]
                        
                    padding = find_padding(pady) + find_padding(padx)
                    print('AutoPadding| size: ', (pady.shape[0], padx.shape[0]), 'padding ', padding)             
                    cfg['padding'] = padding
                    img = img[padding[0]: img.shape[0] - padding[1], padding[2] : img.shape[1] - padding[3]]
                    auto_padding = False
                    
                img_time = time.perf_counter()
                pil_img = Image.fromarray(img[...,::-1])
                
                # change group
                ldtag.configure(text=gm.get_group())
                
                # detect game state
                gm.check_img(img, img_time)
                if last_mode != gm.mode:
                    f.clear()
                    graff.clear()
                    adb.release_all_keys()
                last_mode = gm.mode
                # check with Fishing manager
                if last_mode in f.mode:
                    action = f.mode[gm.mode](img, img_time)
                elif last_mode in gene.mode:
                    gene.scan(img, last_mode)
                    action = []
                    time.sleep(0.1)
                elif last_mode in graff.mode:
                    action = graff.action(gm.mode, img)
                    time.sleep(0.1)
                else:
                    action = []
                
                # print(action)
                adb.parse_action(action)
                if do_test == 'u':
                    gene.scan_green_gene(img)
                if do_test == 'i':
                    gene.scan_blue_gene(img)
                if do_test == 'o':
                    gene.scan_red_gene(img)
                do_test = False
                    
                if save_img:
                    now = datetime.now()
                    date_time = now.strftime("./%H-%M-%S")
                    pil_img.save(date_time + ".png")
                    save_img = False
                
                
                if gm.game_group == 1:
                    main_text = '\n'.join([gm.text, gene.text])
                    display = gene.display
                else:
                    main_text = gm.text
                    display = Image.fromarray(np.hstack([cv2.resize(img, (534, 300)), f.display])[...,::-1])
                    
                pil_img = display
                
                # print(gm.mode)
                # update the display
                imgtk = ImageTk.PhotoImage(image=pil_img)
                lmain.imgtk = imgtk
                lmain.configure(image=imgtk)
                ldres.configure(text=main_text)
                
            lmain.after(display_interval, capture_stream) 

        capture_stream()
        root.mainloop()
    gm.close()
    adb.stop_loop()

def usage():
    print("AutoCatPlanet操作说明:\nS:保存当前截图\nP:估计config中padding的数值,建议得到结果后手动更改config.json\n空格:暂停/恢复\nQ:退出\n" + '-'*8)


if __name__ == '__main__':
    usage()
    cfg = load_cfg()
    main(cfg)
