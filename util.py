# -*- coding:utf-8 -*-
import json
import win32gui


def load_cfg():
    with open('./config.json', 'r', encoding="utf-8") as f:
        content = f.read()
        cfg = json.loads(content)
        return cfg


def get_possible_window_name(name="MuMu模拟器"):
    print("Search for the window whose name contains", name)
    possible_hwnd = None
    def winEnumHandler(hwnd, ctx):
        nonlocal possible_hwnd
        if win32gui.IsWindowVisible(hwnd):
            win_name = win32gui.GetWindowText(hwnd)
            if name in win_name:
                possible_hwnd = hwnd
    win32gui.EnumWindows(winEnumHandler, None)
    if possible_hwnd is None:
        print("Window not found")
    print('-' * 8)
    return possible_hwnd
    
    
def crop_image_by_pts(img, pts):
    h, w = img.shape[:2]
    h1, h2 = int(pts[1] * h), int(pts[3] * h)
    w1, w2 = int(pts[0] * w), int(pts[2] * w)
    return img[h1:h2, w1:w2]


def get_window_roi(name, pos, padding):
    x1, y1, x2, y2 = pos
    ptop, pdown, pleft, pright = padding
    handle = win32gui.FindWindow(0, name)
    # print(handle)
    # handle = 0xd0ea6
    if not handle:
        print("Can't not find " + name)
        handle = get_possible_window_name()

    if handle is None:
        return {'top': -1, 'left': -1, 'width': 100, 'height': 100}
        
    window_rect = win32gui.GetWindowRect(handle)
    
    w = window_rect[2] - window_rect[0] - pleft - pright
    h = window_rect[3] - window_rect[1] - ptop - pdown
    
    window_dict = {
        'left': window_rect[0] + int(x1 * w) + pleft,
        'top': window_rect[1] + int(y1 * h) + ptop,
        'width': int((x2 - x1) * w),
        'height': int((y2 - y1) * h)
    }
    
    return window_dict
    
    
if __name__ == '__main__':
    print("Resize images")
    import glob 
    import cv2 as cv
    imgs = glob.glob('img/*.png')
    
    for i in imgs:
        img = cv.imread(i, 0)
        if img.shape[1] > 1024:
            print(f"Process {i}")
            img = cv.resize(img, (1024, 576))
            cv.imwrite(i, img)
    
    