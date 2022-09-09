from util import *
import numpy as np
import time
import cv2

# 刷涂鸦用
class GraffitiManager:

    def __init__(self, config):
        self.display = np.zeros([300, 300, 3], dtype=np.uint8)
        self.config = config["graffiti"]
        self.mode = {
            20: (0.813, 0.853, 0.895, 0.915),
            21: (0.70, 0.14, 0.75, 0.22),
            22: (0.70, 0.47, 0.75, 0.55),
            23: (0.45, 0.45, 0.55, 0.55),
            24: self.auto_start_battle,
            25: self.remove_selection,
            26: (0.85, 0.9, 0.9, 0.95),
            27: (0.706, 0.660, 0.744, 0.744),
            28: (0.28, 0.70, 0.30, 0.77),
            31: self.new_selection,
            32: self.new_selection,
            33: self.new_selection,
            34: self.new_selection,
            50: (0.5, 0.65, 0.9, 0.71),
            
        }
        self.tapped = False
        self.src = cv2.imread('./img/graffselect.png')[:, :, 1]
        
    def clear(self):
        self.tapped = False
        
    def tap(self, c):
        if self.tapped:
            return []
        self.tapped = True
        x, y = np.random.uniform(c[0], c[2]), np.random.uniform(c[1], c[3])
        return [("tap", (x, y)), ("wait", 1)]


    def action(self, mode, img):
        code = self.mode[mode]
        # 根据按键
        if isinstance(code, tuple):
            return self.tap(code)
        else:
            return code(mode, img)
        
    def auto_start_battle(self, mode, img):
        if self.tapped:
            return []
        self.tapped = True
        return [("tap", (np.random.uniform(0.89, 0.96), np.random.uniform(0.75, 0.79))), ('wait', 0.8), ("tap", (np.random.uniform(0.78, 0.96), np.random.uniform(0.89, 0.94))), ('wait', 0.8)]
        
    def remove_selection(self, mode, img):
        if self.tapped:
            return []
        res = self.tap((0.82, 0.3, 0.97, 0.5))
        res.append(('wait', 1))
        # remove old
        for i in range(4):
            res.append(("tap", (np.random.uniform(0.43, 0.45) + i * 0.13, np.random.uniform(0.24, 0.27))))
            res.append(('wait', np.random.uniform(0.5, 1)))
        self.tapped = True
        return res
            
    def new_selection(self, mode, img):  
        if self.tapped:
            return []
        res = []
        # select new
        for row, col in self.config[f'select{mode % 10}']:
            row -= 1
            col -= 1
            
            src = crop_image_by_pts(self.src, (0.35 + 0.13 * col, 0.23 + 0.27 * row, 0.44 +  0.13 * col,  0.34 + 0.27 * row))
            ratio = img.shape[0] / self.src.shape[0]
            src = cv2.resize(src, (int(src.shape[1] * ratio), int(src.shape[0] * ratio)))
            loc = cv2.matchTemplate(src, img[:, :, 1], cv2.TM_CCOEFF_NORMED)
            min_val,max_val,min_indx,max_indx = cv2.minMaxLoc(loc)
            
            """
            imgc = img.astype(np.uint8).copy() 
            imgc = cv2.circle(imgc, max_indx, 5, (0, 0, 255, 0), 2)
            cv2.imshow('tgt', imgc)
            cv2.waitKey(0)
            """
            res.append(("tap", (np.random.uniform(max_indx[0] + src.shape[1] / 2, max_indx[0] + src.shape[0] / 2 + 50) / img.shape[1],
                                np.random.uniform(max_indx[1] + src.shape[0] / 2, max_indx[1] + src.shape[1] / 2 + 50) / img.shape[0])))
            res.append(('wait', np.random.uniform(0.5, 1)))
            
        # confirm
        res.append(('tap', (np.random.uniform(0.85, 0.96), np.random.uniform(0.9, 0.96))))
        res.append(('wait', np.random.uniform(1, 2)))
        self.tapped = True
        return res
        
 