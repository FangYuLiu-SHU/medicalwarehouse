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

# 2模型输入参数加载模型
K = 90  # history 35
L = 6  # 分类数
in_dim = 57
rows = 2560
HIDDEN_SIZE = K
BATCH_SIZE = 10
EPOCH = 1000  # iteration times
# 定义模型
class FCLSTM(nn.Module):
    def __init__(self):
        super(FCLSTM, self).__init__()
        #输入维度in_dim=57
        self.rnn = nn.LSTM(in_dim, HIDDEN_SIZE, batch_first=True)
        self.layer = nn.Sequential(nn.Linear(HIDDEN_SIZE, int(HIDDEN_SIZE / 2)),
                                   nn.ReLU(True),
                                   nn.Linear(int(HIDDEN_SIZE / 2), L),
                                   nn.Softmax(1))

    def forward(self, x):
        x, _ = self.rnn(x)  # b,K,HIDDEN_SIZE
        x = self.layer(x[:, -1, :])  # b,L
        return x