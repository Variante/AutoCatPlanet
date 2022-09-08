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
            25: (0.82, 0.3, 0.97, 0.5),
            26: (0.85, 0.9, 0.9, 0.95),
            27: (0.706, 0.660, 0.744, 0.744),
            28: (0.28, 0.70, 0.30, 0.77),
            31: self.renew_selection,
            32: self.renew_selection,
            33: self.renew_selection,
            34: self.renew_selection,
            50: (0.5, 0.65, 0.9, 0.71),
            
        }
        self.tapped = False
        
    def clear(self):
        self.tapped = False
        
    def tap(self, x, y):
        if self.tapped:
            return []
        self.tapped = True
        return [("tap", (x, y)), ("wait", 1)]
        
    def action(self, mode, img):
        code = self.mode[mode]
        # 根据按键
        if isinstance(code, tuple):
            def random_code(c):
                return (np.random.uniform(c[0], c[2]), np.random.uniform(c[1], c[3]))
            return self.tap(*random_code(code))
        else:
            return code(mode, img)
        
    def auto_start_battle(self, mode, img):
        if self.tapped:
            return []
        self.tapped = True
        return [("tap", (np.random.uniform(0.88, 0.96), np.random.uniform(0.75, 0.79))), ('wait', 0.8), ("tap", (np.random.uniform(0.78, 0.96), np.random.uniform(0.89, 0.94))), ('wait', 0.8)]
        
    def renew_selection(self, mode, img):
        if self.tapped:
            return []
        res = []
        # remove old
        for i in range(4):
            res.append(("tap", (np.random.uniform(0.43, 0.45) + i * 0.13, np.random.uniform(0.24, 0.27))))
            res.append(('wait', np.random.uniform(0.5, 1)))
        
        # select new
        for row, col in self.config[f'select{mode % 10}']:
            row -= 1
            col -= 1
            res.append(("tap", (np.random.uniform(0.37, 0.41) + col * 0.13, np.random.uniform(0.3, 0.37) + row * 0.28)))
            res.append(('wait', np.random.uniform(0.5, 1)))
            
        # confirm
        res.append(('tap', (np.random.uniform(0.85, 0.96), np.random.uniform(0.9, 0.96))))
        res.append(('wait', np.random.uniform(1, 2)))
        self.tapped = True
        return res