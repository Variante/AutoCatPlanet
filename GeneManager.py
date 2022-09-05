import json
import cv2
import numpy as np
from util import *
from PIL import Image, ImageDraw, ImageFont, ImageTk

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
        
        self.mode = [10, 11, 12, 13]
        self.last_ocr = None
        self.last_other_ocr = None
        self.display = Image.new(mode="RGB", size=(834, 300),  color = (200, 200, 200))
        self.part = ['眼睛', '嘴巴', '花纹', '肤色', '耳朵', '尾巴', '猫种']
        self.text = ''
        self.my_theme_text = ''
        
        self.my_tag = None
        self.other_tag = None
        
    def save_gene(self, file='./db/gene.json'):
        with open(file, 'w', encoding="utf-8") as f:
            json.dump(self.data, f, sort_keys=True, indent=4, ensure_ascii=False) 
        print('json saved')
        
        
    def scan(self, img, mode):
        if mode == 13:
            self.my_tag = None
            self.other_tag = None
            return 
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
        
        last = self.last_other_ocr if mode == 12 else self.last_ocr
        
        if last is not None:
            d = np.mean(np.abs(cmp_ocr - last))
        else:
            d = 1
            
        if mode == 12:
            self.last_other_ocr = cmp_ocr
        else:
            self.last_ocr = cmp_ocr
            
        if d < 1e-5:
            return
            
        tp, tags = self._scan_my_cat(to_ocr)
        if len(tags) > 6 or len(tp) != 1:
            # print("检测出现问题", tp, tags)
            return
            
        if mode == 12:
            self.other_tag = (tp, tags)
        else:
            # 检测自己的猫球主题
            self.my_tag = (tp, tags)
            self.my_theme_text = self.find_theme((tp, tags), strict=False)
        
        # GUI
        display = Image.new(mode="RGB", size=(834, 300),  color = (240, 240, 240))
        font = ImageFont.truetype('./db/NotoSansSC-Medium.otf', 18)
        s_font = ImageFont.truetype('./db/NotoSansSC-Medium.otf', 14)
        ss_font = ImageFont.truetype('./db/NotoSansSC-Medium.otf', 12)
        
        draw = ImageDraw.Draw(display)
        for i, j in enumerate(self.part):
            draw.text((15, 30 * i + 50),  j, font=font, fill=(40, 40, 40))
            
        draw.text((80, 20),  '我的', font=font, fill=(40, 40, 40))
        draw.text((160, 20),  '配对', font=font, fill=(40, 40, 40))
        draw.text((240, 20),  '可能的基因', font=font, fill=(40, 40, 40))
        
        
        def draw_tag(t, px):
            pos, color = get_tag_info(t)
            draw.text((px, pos * 30 + 55),  t, font=s_font, fill=color)
            
        def get_tag_info(t):
            if t in self.data['type']:
                color = (40, 40, 40)
                pos = 6
            else:
                color = (46, 141, 221) if t in self.data['blue'] else (93, 163, 117)
                pos = self.data['blue'][i]['pos'] if t in self.data['blue'] else self.data['green'][i]['pos']
            return pos, color
        
        text = '-' * 8
        if self.my_tag is not None:
            # text += f"\n我的猫球: [{self.my_tag[0][0]}]{' '.join(self.my_tag[1])}"
            for i in self.my_tag[1] + self.my_tag[0]:
                draw_tag(i, 80)
        if self.other_tag is not None:
            # text += f"\n配对猫球: [{self.other_tag[0][0]}]{' '.join(self.other_tag[1])}"
            
            for i in self.other_tag[1] + self.other_tag[0]:
                draw_tag(i, 160)
        text += '\n我的猫球主题:\n' + self.my_theme_text
        
        
        if self.my_tag and self.other_tag:
            # text += '\n' + '-' * 8 + '\n'
            gene_text, type_list, gene_list = self.predict_gene()
            # text += gene_text
            
            # 绘制可能出现的基因
            px = [0] * 7
            for i in gene_list:
                pos, color = get_tag_info(i)
                if px[pos] < 3:
                    draw.text((px[pos] * 80 + 240, pos * 30 + 49),  i, font=ss_font, fill=color)
                else:
                    draw.text(((px[pos] - 3) * 80 + 240, pos * 30 + 61),  i, font=ss_font, fill=color)
                px[pos] += 1
                
            for i in type_list:
                draw.text((px[6] * 80 + 240, 6 * 30 + 55),  i, font=s_font, fill=(40, 40, 40))
                px[6] += 1
                
            # 绘制主题得分
            draw.text((480, 20),  '可能的主题得分', font=font, fill=(40, 40, 40))
            scores = self.find_theme((type_list, gene_list), strict=True).split('\n\n')
            line = -1
            for i, s in enumerate(scores):
                line += 1
                m_tags = s.split()
                draw.text((480, line * 18 + 49),  m_tags[0], font=ss_font, fill=(max(255 - i * 20, 0), 40, 40))
                for t, j in enumerate(m_tags[2:]):
                    draw.text((560 if t % 2 == 0 else 720, line * 18 + 49),  j, font=ss_font, fill=(max(255 - i * 20, 0), 40, 40))
                    if t % 2 == 1:
                        line += 1
            
                
            
        self.text = text
        self.display = display
        
        
    def _scan_my_cat(self, img):
        # print('检测标签')
        tags = self.ocrapp.ocr(img)
        if len(tags) < 1:
            return [], []
        if tags[0]['text'] not in self.data['type']:
            return [], []
        # print(tags)
        # cv2.imshow('detect', img)
        # cv2.waitKey(1)
        return [tags[0]['text']], [i['text'] for i in tags[1:] if i['text'] in self.data['blue'] or i['text'] in self.data['green']]
        
    
    def predict_gene(self):
        possible_tp = set(self.my_tag[0] + self.other_tag[0])
        text = f"可能的猫种: {','.join(list(possible_tp))}\n" 
        
        gene = [set() for _ in range(6)]
        
        # 可能出现的基因
        for i in self.my_tag[1] + self.other_tag[1]:
            # 现有的绿
            if i in self.data['green']:
                pos = self.data['green'][i]['pos']
                gene[pos].add(i)
                
        # 组合的蓝
        for i in self.data['blue']:
            pos = self.data['blue'][i]['pos']
            if i not in gene[pos]:
                for j in self.data['blue'][i]['pre']:
                    if j not in gene[pos]: # 没有绿基因
                        break
                else:
                    ts = set(self.data['blue'][i]['type']).intersection(possible_tp)
                    # print(i, ts, self.data['blue'][i])
                    # 猫种允许，添加
                    if len(ts) > 0:
                        gene[pos].add(i)
                    else:
                        pass
                        # print("猫种不允许", self.data['blue'][i]['type'], possible_tp, self.data['blue'][i]['pre'])
        
        # 可能出现的基因
        for i in self.my_tag[1] + self.other_tag[1]:
            # 现有的蓝
            if i in self.data['blue']:
                pos = self.data['blue'][i]['pos']
                gene[pos].add(i)
                gene[pos].update(self.data['blue'][i]['pre'])

        
        
        biggene = []
        text += '可能的基因:\n'
        for j, i in enumerate(gene):
            p = list(i)
            p.sort(key=lambda x: 0 if x in self.data['blue'] else 1)
            text += self.part[j] + ':' + ','.join(p) + '\n'
            biggene.extend(p)
            
            
            
        # text += '-' * 8 + '\n可能的主题得分:\n' + self.find_theme((possible_tp, biggene))
        
        return text, possible_tp, biggene
    
    def find_theme(self, source, strict):
        want_text = []
        text = []
        # print('-' * 8)
        def to_text(theme, score, need_text):
            if len(need_text):
                return f'{theme}({score}) 需求: {need_text}'
            else:
                return f'{theme}({score}): 已达成'
        
        
        for i in self.data['red']:
            if i in self.config['ignore']:
                continue
            score, need_text = self._plan(source, i, strict)
            
            if i in self.config['want']:
                want_text.append((i, score, need_text))
            else:
                text.append((i, score, need_text))
                
        want_text.sort(key=lambda x: x[1], reverse=True)
        wt = [to_text(*i) for i in want_text]
        
        text.sort(key=lambda x: x[1], reverse=True)
        t = [to_text(*i) for i in text[:self.config['display']]]
        
        return '\n\n'.join(wt + t)
        
        
    def _plan(self, source, target, strict=False):
        tp, tags = source
        score = 0
        tgt = self.data['red'][target]
        
        need_text = ''
        
        # 猫种相同
        if tgt['type'][0] in tp:
            score += self.config['type_score']
        else:
            need_text += f"[{tgt['type'][0]}]"
            if strict:
                need_text = "猫种不匹配"
                return -100, need_text
        
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
                        if len(set(tp).intersection(tgt_p['type'])) > 0:
                            score += self.config['type_score']
                        need_text += f" {pre}({'/'.join([i for i in tgt_p['pre'] if i != pre_p])})"
                            
                        break
                else:
                    # 一个基因都没有
                    need_text += f" {pre}({'/'.join(tgt_p['pre'])})"
        # print(score, need_text)
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
