from util import *
import numpy as np
import cv2
import random
# import scipy.stats

# 钓鱼用
class FishingManager:

    def __init__(self, config):
        # self.chart = None
        self.display = np.zeros([300, 300, 3], dtype=np.uint8)
        self.config = config["fishing"]
        self.last_circle_idx = 0
        self.last_time = 0
        self.band_idx = (0, 0)
        self.tapped = False
        self.counter = 0
        self.pull_counter = 0
        self.mode = {
            1: self.check_circle,
            2: self.check_pull,
            3: self.just_tap,
            4: self.start_tap,
            5: self.center_tap,
        }
        self.drop = False
        self.drop_count = 0
        self.fish_count = 0
        
        # self.font = cv2.FONT_HERSHEY_SIMPLEX
        
    def clear(self):
        self.last_circle_idx = 0
        self.band_idx = (0, 0)
        self.last_time = 0
        self.tapped = False
        self.drop = False
        self.counter = 0
        self.pull_counter = 0
        
    def tap(self, x, y):
        self.counter += 1
        if not self.tapped or self.counter > 30:
            res = ("tap", (x, y))
            self.counter = 0
        else:
            res = []
        self.tapped = True
        return res
        
    def center_tap(self, img, img_time):
        return self.tap(random.random() / 20 + 0.473, random.random() / 10 + 0.419)
        
    def start_tap(self, img, img_time):
        self.fish_count += 1 # 钓鱼次数计数
        
        if self.fish_count > 30:
            self.fish_count = 0
            # 补充材料
        
        return self.tap(random.random() / 10 + 0.88, random.random() / 10 + 0.8)
        
    def just_tap(self, img, img_time):
        self.drop_count = 0 # 鱼上岸，清空计数器
        return self.tap(random.random() / 10 + 0.445, random.random() / 12 + 0.78)
        
    def check_pull(self, img, img_time):
        # 和🐟的拉扯
        self.last_time = img_time
        h, w, _ = img.shape
        
        if self.drop:
            return ("release", (0.9, 0.85))
            
        self.pull_counter += 1
        if self.config["drop_cheap_fish"] and self.drop_count < self.config['drop_until']: # 只在连续失败次数小于的时候检测
            green = img[int(h * 0.272), int(w * 0.53), 1] 
            # print(green, self.pull_counter)
            if green < 240 and self.pull_counter < self.config["drop_thre"]:
                self.drop = True
                self.drop_count += 1
                print(f"血条下降太快，抛弃鱼，第{self.drop_count}/{self.config['drop_until']}次")
                # 血条下降太快
                return ("release", (0.9, 0.85))
        
        
        crop_img = cv2.resize(img[int(h * 0.2): int(h * 0.35), int(w * 0.68): int(w * 0.8)], (150, 100))
        M = cv2.getRotationMatrix2D((10, 50), 25, 1.0)
        rotated = cv2.warpAffine(crop_img[..., 0], M, (80, 30))[5:, 10:]
        thre = rotated.copy()
        thre[rotated < 200] = 0
        
        value = np.mean(thre)
        self.display[:thre.shape[0], :thre.shape[1]] = np.transpose(np.tile(thre, (3, 1, 1)), (1, 2, 0))
            # self.display = cv2.putText(self.display, f'M:{value:.1f}', (50, 50), self.font, 1, 255, 2)
        
        press = True
        if value > self.config['pull_release']:
            press = False
       
       
        def value_to_idx(val):
            ratio = 1 - min((val / self.config['pull_release']) / 4, 1)
            return int(ratio * (self.display.shape[0] - 1))
        
        self.display[:, :-1] = self.display[:, 1:] 
        self.display[:, -1] = 0
        self.display[value_to_idx(value):, -1] = 128 + (-30 if press else 30)
        self.display[value_to_idx(self.config['pull_release']), -1] = 200
            
        
        # print(value)
        # print(rotated.shape)
        # cv2.imshow('Pull', np.vstack([rotated, thre]))
        # cv2.waitKey(0)
        return ("press" if press else "release", (0.9, 0.85)) # 如果不使用虚拟按键
        # return { "press" if press else "release": None }

    def check_circle(self, img, img_time):
        # 抛竿时机的把握
        if self.tapped:
            return []
        h, w, _ = img.shape
        crop_img = cv2.resize(img[int(h * 0.495): int(h * 0.505), int(w * 0.5): int(w * 0.7)], (300, 10))
        rot_img = np.rot90(crop_img, 3)
        
        crop_img = crop_img[..., 0]
        band = np.zeros(crop_img.shape, dtype=np.uint8)
        circle = np.zeros(crop_img.shape, dtype=np.uint8)
        band[(crop_img > 165) & (crop_img < 180)] = 1
        circle[crop_img > 180] = 1
        tap = False
        circle_idx = 0
        
        start_idx = 120
        end_idx = 180
        
        def find_center(patch):
            s = np.sum(patch)
            if s == 0:
                # print("检测不到钓鱼环")
                return 0
            idx = np.repeat(np.arange(patch.shape[1]).reshape(1, -1), patch.shape[0], axis =0) 
            return int(np.sum(idx * patch) / s)
            
        def find_range(patch, start_idx, end_idx):
            patch = patch[:, start_idx: end_idx]
            if np.max(patch) == 0:
                # print("检测不到环带")
                return 0, 1
                # results_dist, proportiontocut=0.25, axis=None)
            return int(np.mean(np.argmax(patch, axis=1)) + start_idx), int(patch.shape[1] - 1 - np.mean(np.argmax(patch[:, ::-1], axis=1)) + start_idx)
        
        enable = True
        if (self.band_idx[1] - self.band_idx[0]) > 20 or (self.band_idx[1] - self.band_idx[0]) < 10 :
            self.band_idx = find_range(band, start_idx, end_idx) 
            enable = False
            # print("检测环带:", self.band_idx)
            
        if self.band_idx[0] > 0:
            # circle speed: ~200 pixel/s
            circle_idx = find_center(circle)
            if self.last_circle_idx > 0:
                # direction
                forward = circle_idx > self.last_circle_idx
                predict = circle_idx + self.config['circle_predict'] * (1 if forward else -1)
                tap = (self.band_idx[0] < predict < self.band_idx[1]) and enable
                # print("Predict: ", predict, circle_idx, 'L', self.band_idx[0], self.band_idx[1])
            if circle_idx > 0:
                self.last_circle_idx = circle_idx
                
        self.last_time = img_time
        
        """
        band[:, band_left_idx] = 255
        band[:, band_right_idx] = 128
        circle[:, circle_idx] = 255
        cv2.imshow('Circle', np.vstack([circle, crop_img, band]))
        cv2.waitKey(0)
        """
        w = rot_img.shape[1]
        self.display[:, -w] = 0
        self.display[:, :-1] = self.display[:, 1:]
        self.display[circle_idx, -w - 1] = 225
        self.display[self.band_idx[0], -w-1] = 128
        self.display[self.band_idx[1], -w-1] = 200
        
        self.display[:, -w:] = rot_img
        self.display[start_idx, -w:] = 225
        self.display[end_idx, -w:] = 225
        if tap:
            self.display[:, -w] += 30
            # self.chart = np.hstack([self.chart[:, w:], rot_img])
        # self.display = np.hstack([self.chart, rot_img])
        # cv2.imshow('Circle', np.hstack([self.chart, np.rot90(crop_img, 3)]))
        # cv2.waitKey(1)
        
        if tap:
            self.tapped = True
            return ("tap", None)
        else:
            return []
        
        
        
        
if __name__ == '__main__':
    cfg = load_cfg()
    f = FishingManager(cfg)
    img = cv2.imread('img/fishingpull.png')
    f.check_pull(img, None)
    