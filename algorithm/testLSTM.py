import pandas as pd
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import optim
import logging
import sys
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from torch import cuda
from torch import nn
from torch import optim
from torch.utils import data
from algorithm.pulsePredictLSTM import Dataset

# 2模型输入参数加载模型
K = 90  # history 35
L = 4  # 分类数
in_dim = 57
rows = 2560
HIDDEN_SIZE = K
BATCH_SIZE = 10
EPOCH = 1000  # iteration times

# 测试模型
# 1 加载模型
net = torch.load("../files/LSTM_predict.plt")
# 2读取测试数据
filePath = '../files/pulse_label_order.csv'
test_set_size = 267
sst_dataset_test = Dataset(0, test_set_size, filePath)
sst_dataloader_test = data.DataLoader(sst_dataset_test, batch_size=BATCH_SIZE, shuffle=True)
# 3 全部测试集测试准确度
correct = 0
total = 0
with torch.no_grad():
    if cuda.is_available():
        for data in sst_dataloader_test:
            images, labels = data
            labels = labels.cuda()
            outputs = net(images.cuda())
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    else:
        for data in sst_dataloader_test:
            images, labels = data
            outputs = net(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
print('Accuracy of the network on the 267 test :%d %%' % (100 * correct / total))