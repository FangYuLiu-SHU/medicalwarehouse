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
from modelLSTM import FCLSTM
from pulsePredictLSTM import Dataset
# from algorithm.modelLSTM import FCLSTM
# from algorithm.pulsePredictLSTM import Dataset

# 2模型输入参数加载模型
N = 64    #每个表分成32份每份 80个
K = 400  # history 35
L = 6  # 分类数
in_dim = 57
rows = 2560
HIDDEN_SIZE = K
BATCH_SIZE = 100
EPOCH = 1000  # iteration times
data_num = 1009#数据量

# 1 加载模型
# rnn_model = torch.load("./LSTM_predict.plt")
# rnn_model = rnn_model.cpu()
rnn_model = FCLSTM()
rnn_model.load_state_dict(torch.load('./files/LSTM_predict.pt'))
rnn_model.eval()
# 2 读取测试数据 data_num个
test_set_size = N #设置每个批读N个
tst_dataset = Dataset(0, data_num)
tst_dataloader = data.DataLoader(tst_dataset, batch_size=test_set_size)#, shuffle=True去除打乱否则数据不对
# 3 全部测试集测试准确度
correct = 0
total = 0
# 对一个病人的N个数据进行统计 求出N个结果中最多的结果作为最后病人的诊断结果
with torch.no_grad():
    for tempdata in tst_dataloader:
        pulse_data, labels, _ = tempdata
        # print(pulse_data.shape)
        outputs = rnn_model(pulse_data)
        # 对一个病人N行6列预测值进行按行相加
        outputs = torch.unsqueeze(torch.sum(outputs,axis =0),dim=0)
        # 得到最大的值的索引
        _, predicted = torch.max(outputs.data, 1)
        # 判断是否和原标签对应
        correct += (predicted == labels[0]).sum().item()
        total += labels.size(0)

print('Accuracy of the network on the '+str(data_num)+' test:%d %%' % (100 * correct / (total/N)))