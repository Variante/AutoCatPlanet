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
            27: self.renew_selection,
            
        }
        self.tapped = False
        
    def clear(self):
        self.tapped = False
        
    def tap(self, x, y):
        if self.tapped:
            return []
        self.tapped = True
        return ("tap", (x, y))
        
    def action(self, mode, img):
        code = self.mode[mode]
        # 根据按键
        if isinstance(code, tuple):
            def random_code(c):
                return (np.random.uniform(c[0], c[2]), np.random.uniform(c[1], c[3]))
            return self.tap(*random_code(code))
        else:
            return code(img)
        
    def auto_start_battle(self, _):
        if self.tapped:
            return []
        self.tapped = True
        return [("tap", (random.random() / 20 + 0.89, random.random() / 20 + 0.75)), ('wait', 0.2), ("tap", (random.random() / 20 + 0.85, random.random() / 10 + 0.90))]
        
    def renew_selection(self, img):
        if self.tapped:
            return []
        res = []
        # remove old
        for i in range(4):
            res.append(("tap", (np.random.uniform(0.424, 0.448) + i * 0.13, np.random.uniform(0.24, 0.27))))
            res.append(('wait', np.random.uniform(0.5, 1)))
        
        # select new
        for i in range(1, 5):
            row, col = self.config[f'select{i}']
            res.append(("tap", (np.random.uniform(0.37, 0.41) + col * 0.12, np.random.uniform(0.3, 0.37) + row * 0.28)))
            res.append(('wait', np.random.uniform(0.5, 1)))
            
        # confirm
        res.append(('tap', (np.random.uniform(0.85, 0.96), np.random.uniform(0.9, 0.96))))
        self.tapped = True
        return res