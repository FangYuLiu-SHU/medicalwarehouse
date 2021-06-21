from PIL import Image
import os

def Image_PreProcessing(figpath, save_path):
    # 待处理图片存储路径
    im = Image.open(figpath)
    # Resize图片大小，入口参数为一个tuple，新的图片大小
    imBackground = im.resize((260, 184))
    print(save_path)
    imBackground.save(save_path, 'JPEG')
    # imBackground.save('data/' + patient + '/' + id + '_processed.jpg', 'JPEG')

def folder_imageprocessing(path, target_path):
    for root, dirs, files in os.walk(path):
        if len(files) != 0:
            for file in files:
                data_path = root + '/' + file
                print(data_path)
                Image_PreProcessing(data_path, target_path + '/' + file.lower())

if __name__ == '__main__':
    path = 'C:/Users/Lenovo/Desktop/医疗数据/医疗数据-整理/肾病舌诊仪RGB'
    target_path = '../static/data/tongueimage/kidney'
    folder_imageprocessing(path, target_path)