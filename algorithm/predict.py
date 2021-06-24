import pandas as pd
import json
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import optim
import logging
import sys
import random
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from torch import cuda
from torch import nn
from torch import optim
from torch.utils import data
from algorithm.modelLSTM import FCLSTM
from algorithm.pulsePredictLSTM import Dataset
# from modelLSTM import FCLSTM
# from pulsePredictLSTM import Dataset

#对应关系
#方案一：沉细-0 细-1 弦-2 弦细-3 滑-4 濡-5
#方案二：其他-0 沉-1 细-2 弦-3
def pulsePrediction(pulseData):
    pulseType=['沉细', '细', '弦', '弦细', '滑', '濡']
    rnn_model = FCLSTM()
    rnn_model.load_state_dict(torch.load('./files/LSTM_predict.pt', map_location='cpu'))
    rnn_model.eval()
    # n = torch.load("./files/LSTM_predict.pt").cpu()
    pulseData = torch.from_numpy(pulseData).to(torch.float32)
    pulseData = torch.unsqueeze(pulseData, dim=0)
    result=rnn_model(pulseData)
    print(result)
    _, maxIndex = torch.max(result.data, 1)
    #print(pulseType[maxIndex])
    return pulseType[maxIndex]

def mulPulsePrediction(testSize,totalSize):
    # 1 加载模型
    rnn_model = FCLSTM()
    rnn_model.load_state_dict(torch.load('./files/LSTM_predict.pt', map_location='cpu'))
    rnn_model.eval()
    # 2读取测试数据 200个
    index = random.randint(0,totalSize-testSize)
    tst_dataset = Dataset(index, index+testSize)
    tst_dataloader = data.DataLoader(tst_dataset, batch_size=testSize, shuffle=True)
    # 3 全部测试集测试准确度
    correct = 0
    total = 0
    predicted=0
    labels=0
    idSet=0
    with torch.no_grad():
        for tempdata in tst_dataloader:
            pulse_data, labels, idSet = tempdata
            outputs = rnn_model(pulse_data)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    return idSet,predicted.numpy(),labels.numpy(),correct,total,round(correct / total, 4)

# id,pv,lv,x,n,a=mulPulsePrediction(200,857)
# print(id)
# print("----------------------------------")
# print(pv)
# print("----------------------------------")
# print(lv)
# print("----------------------------------")
# print(x)
# print("----------------------------------")
# print(n)
# print("----------------------------------")
# print(a)
# print("----------------------------------")