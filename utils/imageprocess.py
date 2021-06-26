from PIL import Image
import os
import numpy as np
import pandas as pd
from torchvision import transforms as T
import matplotlib.pyplot as plt
import torch
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def Image_PreProcessing(figpath, save_path):
    # 待处理图片存储路径
    im = Image.open(figpath)
    # Resize图片大小，入口参数为一个tuple，新的图片大小
    imBackground = im.resize((260, 184))
    print(save_path)
    imBackground.save(save_path, 'BMP')
    # imBackground.save('data/' + patient + '/' + id + '_processed.jpg', 'JPEG')

def folder_imageprocessing(path, target_path):
    for root, dirs, files in os.walk(path):
        if len(files) != 0:
            for file in files:
                data_path = root + '/' + file
                print(data_path)
                Image_PreProcessing(data_path, target_path + '/' + file.lower())

class ImgAugmentation():
    def __init__(self, image_folder_path, label_path):
        self.image_folder_path = image_folder_path
        self.label_path = label_path

        self.pd_labels = self.load_label_data()

        # 变换类型
        # 随机水平翻转
        self.transform_H = T.Compose([
            T.RandomHorizontalFlip(p=1),
            T.ToTensor(),
        ])
        # 随机上下翻转
        self.transform_V = T.Compose([
            T.RandomVerticalFlip(p=1),
            T.ToTensor(),
        ])
        # 随机剪切
        self.transform_C = T.Compose([
            T.RandomResizedCrop(size=(260, 184), scale=(0.4, 1.0), ratio=(0.75, 1.3333333333333333)),
            T.ToTensor(),
        ])
        # 中心剪裁
        self.transform_CC = T.Compose([
            T.CenterCrop(size=150),
            T.ToTensor(),
        ])
        # 随机改变亮度
        self.transform_bright = T.Compose([
            T.ColorJitter(brightness=0.5, contrast=0, saturation=0, hue=0),  # 亮度为50%-150%,
            T.ToTensor(),
        ])
        # 随机对比度
        self.transform_contrast = T.Compose([
            T.ColorJitter(brightness=0, contrast=0.5, saturation=0, hue=0), # 对比度为50%-150%
            T.ToTensor(),
        ])
        # 随机饱和度
        self.transform_sat = T.Compose([
            T.ColorJitter(brightness=0, contrast=0, saturation=0.5, hue=0), # 饱和度为50%-150%
            T.ToTensor(),
        ])
        # 随机旋转
        self.transform_rot = T.Compose([
            T.RandomRotation(degrees=60, expand=False, fill=0),
            T.ToTensor(),
        ])

    def load_label_data(self):
        pd_labels = pd.read_csv(self.label_path)
        # print(pd_labels)
        return pd_labels

    def one_img_augment(self, img_path, nums=[2,2,2,2,2,2,5]):
        image = Image.open(img_path)
        # image.show()

        H_images = self.apply(image, transforms=self.transform_H, num=nums[0])
        V_images = self.apply(image, transforms=self.transform_V, num=nums[1])
        C_images = self.apply(image, transforms=self.transform_C, num=nums[2])
        contrast_images = self.apply(image, transforms=self.transform_contrast, num=nums[3])
        bright_images = self.apply(image, transforms=self.transform_bright, num=nums[4])
        sat_images = self.apply(image, transforms=self.transform_sat, num=nums[5])
        rot_images = self.apply(image, transforms=self.transform_rot, num=nums[6])
        trans_images = H_images+V_images+C_images+contrast_images+bright_images+sat_images+rot_images
        print(len(trans_images), trans_images)
        # self.show_images(trans_images, 7, 1)

        return trans_images


    def apply(self, original_img, transforms=None, num=8):
        """
        对图像多次运用图像增广方法并展示所有结果
        """
        if num == 0:
            return []
        for i in range(num):
            img = transforms(original_img)
            img = img.reshape(1, *img.shape)
            if i == 0:
                imgs = img
            else:
                imgs = torch.cat([imgs, img], 0)
        pil_imgs = []
        for i in range(imgs.shape[0]):
            img = T.ToPILImage()(imgs[i])
            # img = T.ToPILImage()(np.uint8(imgs[i]).transpose(2,1,0))
            pil_imgs.append(img)
        # self.show_images(pil_imgs, num,1)
        return pil_imgs



    def show_images(self, imgs, num_rows, num_cols, scale=2):
        # figsize = (num_cols * scale, num_rows * scale)
        # _, axes = plt.subplots(num_rows, num_cols, figsize=figsize)
        fig = plt.figure()
        # 建立子图
        axes = fig.subplots(num_rows, num_cols)

        for i in range(num_rows):
            for j in range(num_cols):
                img = imgs[i * num_cols + j]
                # print(type(axes[i * num_cols + j]))
                axes[i * num_cols + j].imshow(img)
        plt.show()
    # def get_datainstance(self):
    #     patient_ids = []
    #     images = []
    #     tongue_colors = []
    #     moss_colors = []
    #     for i in range(len(self.pd_labels)):
    #         patient_id = self.pd_labels.loc[i, 'id']
    #         tongue_color = self.pd_labels.loc[i, 'tongue_proper_color']
    #         moss_color = self.pd_labels.loc[i, 'tongue_moss_color']
    #         # print(patient_id, tongue_color)
    #         image_path = os.path.join(self.image_folder_path, patient_id.lower() + '.bmp')
    #         # print(image_path)
    #         if os.path.exists(image_path):
    #             img_np = self.load_image_data(image_path)
    #             # print(img_np)
    #             patient_ids.append(patient_id)
    #             images.append(img_np)
    #             tongue_colors.append(tongue_color)
    #             moss_colors.append(moss_color)
    #     # print(images)
    #     # print(labels)
    #     return patient_ids, images, tongue_colors, moss_colors

    def produce_aug_imgs(self):
        pd_labels_aug = pd.DataFrame(columns=self.pd_labels.columns)
        for i in range(len(self.pd_labels)):
            patient_id = self.pd_labels.loc[i, 'id']
            tongue_color = self.pd_labels.loc[i, 'tongue_proper_color']
            moss_color = self.pd_labels.loc[i, 'tongue_moss_color']
            image_path = os.path.join(self.image_folder_path, patient_id.lower() + '.bmp')
            if os.path.exists(image_path):
                pd_labels_aug = pd_labels_aug.append(self.pd_labels.loc[i, :], ignore_index=True)
                aug_list = []
                if tongue_color == 0:
                    aug_list = [1, 1, 2, 1, 0, 0, 5]
                elif tongue_color == 1:
                    aug_list = [1, 0, 0, 0, 0, 0, 0]
                elif tongue_color == 2:
                    aug_list = [1, 1, 2, 1, 0, 0, 5]
                else:
                    aug_list = [2, 2, 2, 1, 0, 0, 5]
                print(image_path, aug_list)
                trans_images = self.one_img_augment(image_path, nums=aug_list)
                n = 1
                for trans_img in trans_images:
                    new_id = patient_id.lower() + '-' + str(n)
                    save_path = os.path.join(self.image_folder_path, new_id + '.bmp')
                    n += 1
                    print(save_path)
                    trans_img.save(save_path, 'BMP')
                    new_label = self.pd_labels.loc[i,:]
                    new_label['id'] = new_id
                    pd_labels_aug = pd_labels_aug.append(new_label, ignore_index=True)
        pd_labels_aug.to_csv('../files/tongue_all_features_aug.csv', index=False)
        print(pd_labels_aug)

    def produce_aug_moss_imgs(self):
        pd_labels_aug = pd.DataFrame(columns=self.pd_labels.columns)
        for i in range(len(self.pd_labels)):
            patient_id = self.pd_labels.loc[i, 'id']
            tongue_color = self.pd_labels.loc[i, 'tongue_proper_color']
            moss_color = self.pd_labels.loc[i, 'tongue_moss_color']
            image_path = os.path.join(self.image_folder_path, patient_id.lower() + '.bmp')
            if os.path.exists(image_path):
                pd_labels_aug = pd_labels_aug.append(self.pd_labels.loc[i, :], ignore_index=True)
                aug_list = []
                if moss_color == 0:
                    aug_list = [1, 0, 0, 0, 0, 0, 0]
                elif moss_color == 1:
                    aug_list = [1, 1, 2, 1, 0, 0, 5]
                print(image_path, aug_list)
                trans_images = self.one_img_augment(image_path, nums=aug_list)
                n = 1
                for trans_img in trans_images:
                    new_id = patient_id.lower() + '-' + str(n)
                    save_path = os.path.join(self.image_folder_path, new_id + '.bmp')
                    n += 1
                    print(save_path)
                    trans_img.save(save_path, 'BMP')
                    new_label = self.pd_labels.loc[i,:]
                    new_label['id'] = new_id
                    pd_labels_aug = pd_labels_aug.append(new_label, ignore_index=True)
        pd_labels_aug.to_csv('../files/moss_all_features_aug.csv', index=False)
        print(pd_labels_aug)



if __name__ == '__main__':
    # path = 'C:/Users/Lenovo/Desktop/医疗数据/医疗数据-整理/肾病舌诊仪RGB'
    # target_path = '../static/data/tongueimage/kidney'
    # folder_imageprocessing(path, target_path)

    # 舌色预测数据增强
    # image_folder_path = '../static/data/tongueimage_aug'
    # label_path = '../files/tongue_all_features.csv'
    # imgaugmentation = ImgAugmentation(image_folder_path, label_path)
    # imgaugmentation.produce_aug_imgs()

    # imgaugmentation.one_img_augment(image_folder_path + '/l0780.bmp')


    # 苔色预测数据增强
    image_folder_path = '../static/data/moss_aug'
    label_path = '../files/tongue_all_features.csv'
    imgaugmentation = ImgAugmentation(image_folder_path, label_path)
    imgaugmentation.produce_aug_moss_imgs()
