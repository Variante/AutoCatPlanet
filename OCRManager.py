

class OCRManager:
    def __init__(self):
        self.ocrapp = None

    def ocr(self, img):
        if self.ocrapp is None:
            print("初次使用加载OCR...")
            from cnocr import CnOcr
            with open('./db/chrset.txt', 'r', encoding='utf-8') as f:
                cand = f.readline()
                # print(cand)
            self.ocrapp = CnOcr(cand_alphabet=cand)
        return self.ocrapp.ocr(img)


if __name__ == '__main__':
    ocr = OCRManager()
