import torch
import torch.utils.data as Data
from torch.utils.data import random_split
import os
from PIL import Image
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE

class Dataloader():
    def __init__(self, image_folder_path, label_path, input_size = 128):
        self.image_folder_path = image_folder_path
        self.label_path = label_path
        self.input_size = input_size

        self.pd_labels = self.load_label_data()


    def load_image_data(self, image_path):
        # print(image_path)
        img = Image.open(image_path)
        img_resize = img.resize((self.input_size, self.input_size))
        img_np = np.array(img_resize).transpose((2, 1, 0))
        # print(img_np, img_np.shape)
        return img_np

    def load_label_data(self):
        pd_labels = pd.read_csv(self.label_path)
        # print(pd_labels)
        return pd_labels

    def get_datainstance(self):
        patient_ids = []
        images = []
        tongue_colors = []
        moss_colors = []
        for i in range(len(self.pd_labels)):
            patient_id = self.pd_labels.loc[i, 'id']
            tongue_color = self.pd_labels.loc[i, 'tongue_proper_color']
            moss_color = self.pd_labels.loc[i, 'tongue_moss_color']
            # print(patient_id, tongue_color)
            image_path = os.path.join(self.image_folder_path, patient_id.lower() + '.bmp')
            # print(image_path)
            if os.path.exists(image_path):
                img_np = self.load_image_data(image_path)
                # print(img_np)
                patient_ids.append(patient_id)
                images.append(img_np)
                tongue_colors.append(tongue_color)
                moss_colors.append(moss_color)
        # print(images)
        # print(labels)
        return patient_ids, images, tongue_colors, moss_colors

    def get_train_test_dataloader(self, batch_size, train_rate=0.8, seed=42):
        patient_ids, images, tongue_colors, moss_colors = self.get_datainstance()
        # self.data_over_sampling(images, tongue_colors)
        data_num = len(patient_ids)
        train_num = round(train_rate * data_num)
        test_num = round((1 - train_rate) * data_num)
        print('data_num:', data_num, ' train_num:', train_num, ' test_num:', test_num)
        print(patient_ids)
        print(tongue_colors)
        # 舌色
        tongue_color_dataset = Data.TensorDataset(torch.LongTensor(images), torch.LongTensor(tongue_colors))
        tongue_color_train_data, tongue_color_test_data = random_split(tongue_color_dataset, [train_num, test_num], generator=torch.Generator().manual_seed(seed))
        tongue_color_train_loader = Data.DataLoader(tongue_color_train_data, batch_size=batch_size, shuffle=True)
        tongue_color_test_loader = Data.DataLoader(tongue_color_test_data, batch_size=batch_size, shuffle=False)

        # 苔色
        moss_color_dataset = Data.TensorDataset(torch.LongTensor(images), torch.LongTensor(moss_colors))
        moss_color_train_data, moss_color_test_data = random_split(moss_color_dataset, [train_num, test_num], generator=torch.Generator().manual_seed(seed))
        moss_color_train_loader = Data.DataLoader(moss_color_train_data, batch_size=batch_size, shuffle=True)
        moss_color_test_loader = Data.DataLoader(moss_color_test_data, batch_size=batch_size, shuffle=False)


        pd_labels = pd.DataFrame(columns=['patient_id', 'tongue_color', 'moss_color'])
        pd_labels['patient_id'] = patient_ids
        pd_labels['tongue_color'] = tongue_colors
        pd_labels['moss_color'] = moss_colors
        print('舌色统计：\n', pd_labels.groupby(by=['tongue_color']).count())
        print('苔色统计：\n', pd_labels.groupby(by=['moss_color']).count())
        return tongue_color_train_loader, tongue_color_test_loader, moss_color_train_loader, moss_color_test_loader

        # img = plt.imread(img_path)
        # img = img.transpose(2,1,0)
        # print(img, img.shape)

        # data_transfrom = transforms.Compose([  # 对读取的图片进行以下指定操作
        #     transforms.Resize((128, 128)),
        #     transforms.ToTensor(),
        # ])
        # images = datasets.ImageFolder(path,)
        # imgLoader = torch.utils.data.DataLoader(images, batch_size=2, shuffle=False, num_workers=1)  # 指定读取配置信息
        # # print(next(iter(imgLoader)))
        # images = imgLoader.images
        # for batch_images, _ in imgLoader:
        #     print(batch_images)


    def data_over_sampling(self, X, Y):
        smo = SMOTE(random_state=0)
        X_smo, Y_smo = smo.fit_resample(X, Y)
        print(X_smo)
        print(Y_smo)
        new_data = pd.concat([Y_smo, X_smo], axis=1)
        print(new_data)



if __name__ == '__main__':
    image_folder_path = '../static/data/tongueimage'
    label_path = '../files/tongue_all_features.csv'
    dataloader = Dataloader(image_folder_path, label_path)

    print(dataloader.pd_labels)

    tongue_color_train_loader, tongue_color_test_loader = dataloader.get_train_test_dataloader(batch_size=8)
    # for batch_id, (batch_imgs, batch_labels) in enumerate(tongue_color_train_loader):
    #     print(batch_id, batch_imgs.size, batch_labels)




