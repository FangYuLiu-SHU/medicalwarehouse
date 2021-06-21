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
K = 90  # history 35
L = 6  # 分类数
in_dim = 57
rows = 2560
HIDDEN_SIZE = K
BATCH_SIZE = 100
EPOCH = 1000  # iteration times

# 1 加载模型
# rnn_model = torch.load("./LSTM_predict.plt")
# rnn_model = rnn_model.cpu()
rnn_model = FCLSTM()
rnn_model.load_state_dict(torch.load('../files/LSTM_predict.pt'))
rnn_model.eval()
# 2读取测试数据 857
test_set_size = 857
tst_dataset = Dataset(0, 857)
tst_dataloader = data.DataLoader(tst_dataset, batch_size=test_set_size, shuffle=True)
# 3 全部测试集测试准确度
correct = 0
total = 0
with torch.no_grad():
    for tempdata in tst_dataloader:
        pulse_data, labels = tempdata
        print(pulse_data.shape)
        outputs = rnn_model(pulse_data)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
print('Accuracy of the network on the 857 test:%d %%' % (100 * correct / total))