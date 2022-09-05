import json
import cv2
import numpy as np
from util import *


class GeneManager:
    def __init__(self, config, ocr):
        self.config = config['gene']
        self.ocrapp = ocr
        
        self.data = load_cfg('./db/gene.json')
        
        print(f"基础基因{len(self.data['green'])}个")
        print(f"组合基因{len(self.data['blue'])}个")
        print(f"主题基因{len(self.data['red'])}个")
        
        """
        self.name_set = set()
        
        
        # 初始化
        for i in ['green', 'red', 'blue']:
            if i not in self.data:
                self.data[i] = {}
            else:
                for j in self.data[i]:
                    self.name_set.add(j)
        
        
        # 重做字符集
        chrs = set()
        for i in ['green', 'blue']:
            for t in self.data[i]:
                for ch in t:
                    chrs.add(ch)
                for ch in self.data[i][t]['type'][0]:
                    chrs.add(ch)
                    
        with open('./db/chrset.txt', 'w', encoding='utf-8') as f:
            for i in chrs:
                f.write(i)
        """
        
        self.mode = [10, 11]
        self.last_ocr = None
        self.text = ''
        
        
    def save_gene(self, file='./db/gene.json'):
        with open(file, 'w', encoding="utf-8") as f:
            json.dump(self.data, f, sort_keys=True, indent=4, ensure_ascii=False) 
        print('json saved')
        
        
    def scan(self, img, mode):
        h, w, _ = img.shape
        if mode == 11:
            img[int(0.3 * h): int(0.533 * h), int(0.05 * w): int(0.324 * w)] = 255 # 掩盖4属性
            img[int(0.256 * h): int(0.29 * h), int(0.133 * w): int(0.09 * w)] = 0 # 掩盖生日
            img[int(0.533 * h): int(0.7 * h), int(0.06 * w): int(0.09 * w)] = 255 # 掩盖两列图标
            img[int(0.533 * h): int(0.7 * h), int(0.19 * w): int(0.23 * w)] = 255
            to_ocr = img[int(0.256 * h): int(0.7 * h), int(0.05 * w): int(0.324 * w), 0]

        else:
            img[int(0.28 * h): int(0.32 * h), int(0.05 * w): int(0.324 * w)] = 255 # 掩盖外观基因
            img[int(0.27 * h): int(0.493 * h), int(0.06 * w): int(0.09 * w)] = 255 # 掩盖两列图标
            img[int(0.27 * h): int(0.493 * h), int(0.19 * w): int(0.23 * w)] = 255
            to_ocr = img[int(0.228 * h): int(0.493 * h), int(0.05 * w): int(0.324 * w), 0]
        
        # 检测帧变化
        cmp_ocr = cv2.resize(to_ocr, (240, 400)) / 255.0
        if self.last_ocr is not None:
            d = np.mean(np.abs(cmp_ocr - self.last_ocr))
        else:
            d = 1
        self.last_ocr = cmp_ocr
        if d < 1e-5:
            return
            
        tp, tags = self._scan_my_cat(to_ocr)
        text = f"检测到: [{tp}]{' '.join(tags)}\n--------\n"
        if len(tags) > 6 or tp not in self.data['type']:
            # print("检测出现问题", tp, tags)
            return
            
        self.text = text + self.find_theme((tp, tags))
        
        
    def _scan_my_cat(self, img):
        # print('检测标签')
        tags = self.ocrapp.ocr(img)
        if len(tags) < 1:
            return '', []
        # print(tags)
        # cv2.imshow('detect', img)
        # cv2.waitKey(1)
        return tags[0]['text'], [i['text'] for i in tags[1:] if i['text'] in self.data['blue'] or i['text'] in self.data['green']]
        
        
    def find_theme(self, source):
        want_text = []
        text = []
        
        def to_text(theme, score, need_text):
            if len(need_text):
                return f'{theme}({score}) 需求: {need_text}'
            else:
                return f'{theme}({score}): 已达成'
        
        
        for i in self.data['red']:
            if i in self.config['ignore']:
                continue
            score, need_text = self._plan(source, i)
            
            if i in self.config['want']:
                want_text.append((i, score, need_text))
            else:
                text.append((i, score, need_text))
                
        want_text.sort(key=lambda x: x[1], reverse=True)
        want_text = [to_text(*i) for i in want_text]
        
        text.sort(key=lambda x: x[1], reverse=True)
        text = [to_text(*i) for i in text[:self.config['display']]]
        
        return '\n\n'.join(want_text + text)
        
        
    def _plan(self, source, target):
        tp, tags = source
        score = 0
        tgt = self.data['red'][target]
        
        need_text = ''
        
        # 猫种相同
        if tgt['type'][0] == tp:
            score += self.config['type_score']
        else:
            need_text += f"[{tgt['type'][0]}]"
        
        for pre in tgt['pre']:
            if pre in tags:
                # 检测蓝色基因
                score += (self.config['blue_score'] + self.config['type_score'])         
            else:
                # 查看不存在的基因的组合
                tgt_p = self.data['blue'][pre]
                for pre_p in tgt_p['pre']:
                    if pre_p in tags:
                        # 符合一个绿色基因
                        score += self.config['green_score']
                        # 蓝色基因的猫种相同
                        if tp in tgt_p['type']:
                            score += self.config['type_score']
                        need_text += f" {pre}({'/'.join([i for i in tgt_p['pre'] if i != pre_p])})"
                            
                        break
                else:
                    # 一个基因都没有
                    need_text += f" {pre}({'/'.join(tgt_p['pre'])})"
        
        return score, need_text
                    
                
        
    def _scan_left(self, img):
        h, w, _ = img.shape
        to_ocr = img[int(0.186 * h): int(0.882 * h), int(0.08 * w): int(0.185 * w), 0]
        tags = self.ocrapp.ocr(to_ocr)
        return tags
        
    def _scan_right(self, img):
        h, w, _ = img.shape
        # block 猫种和合成所需基因
        img[int(0.246 * h): int(0.279 * h), int(0.71 * w): int(0.751 * w)] = 0
        img[: int(0.271 * h), int(0.895 * w): w] = 0
        img[int(0.292 * h): int(0.326 * h), int(0.71 * w): int(0.795 * w)] = 255
        img[int(0.292 * h): h, int(0.85 * w): int(0.88 * w)] = 255
        img[int(0.292 * h): h, int(0.71 * w): int(0.74 * w)] = 255
        to_ocr = img[int(0.179 * h): int(0.51 * h), int(0.71 * w): int(0.98 * w), 0]
        
        tags = self.ocrapp.ocr(to_ocr)
        return tags
        
    def scan_green_gene(self, img):
        for tag in self._scan_left(img):
            text = tag['text']
            if len(text) < 3 or len(text.strip()) != len(text):
                continue
            if text not in self.data['green']:
                self.data['green'][text] = {
                    'type': ['狸花', '美短', '布偶', '三花'],
                    'pre': [],
                }
                print(f"增加 {text}, 现在一共{len(self.data['green'])}个")
                
        self.save_gene()
        
    def scan_red_gene(self, img):
        name, info = self._scan_combo(img, 8, 1)
        if isinstance(info, list):
            print(info)
            return
        if name not in self.data['red']:
            self.data['red'][name] = info
            print(f"增加 {name}-{info}, 现在一共{self.data['red']}个")
            self.save_gene()
        
        
    def scan_blue_gene(self, img):
        name, info = self._scan_combo(img, 4, 3)
        if isinstance(info, list):
            print(info)
            return
        if name not in self.data['blue']:
            self.data['blue'][name] = info
            print(f"增加 {name}-{info}, 现在一共{self.data['blue']}个")
            self.save_gene()
    
    
    def _scan_combo(self, img, n_tag, n_type):
        tags = self._scan_right(img)
        if len(tags) != n_tag:
            print("总标签数量不符")
            return None, tags
            
        text = tags[0]['text']
        tpstr = tags[1]['text'].split('、')
        if len(tpstr) != n_type:
            print("小标签数量不符")
            return None, tags
        pre = [i['text'] for i in tags[2:]]
        for i in pre:
            if i not in self.name_set:
                print(f'{i} 不在已知集合')
                return tags
        return text, {
            'type': tpstr,
            'pre': pre
        }
