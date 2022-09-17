from cnocr import CnOcr

class OCRManager:
    def __init__(self):
        with open('./db/chrset.txt', 'r', encoding='utf-8') as f:
            cand = f.readline()
        self.ocrapp = CnOcr(cand_alphabet=cand)

    def ocr(self, img):
        return self.ocrapp.ocr(img)


if __name__ == '__main__':
    ocr = OCRManager()
