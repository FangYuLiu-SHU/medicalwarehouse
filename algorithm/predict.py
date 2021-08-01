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
from algorithm.TestDataset import TestDataset
# from modelLSTM import FCLSTM
# from pulsePredictLSTM import Dataset

N = 64  # 每个表分成64份每份 40个
#对应关系
#方案一：沉细-0 细-1 弦-2 弦细-3 滑-4 濡-5
#方案二：其他-0 沉-1 细-2 弦-3
def pulsePrediction(pulseData):
    # pulseData输入np类型[[1，2，3]]
    pulseType=['沉细', '细', '弦', '弦细', '滑', '濡']
    rnn_model = FCLSTM()
    rnn_model.load_state_dict(torch.load('./files/LSTM_predict.pt',map_location='cpu'))
    rnn_model.eval()
    # n = torch.load("./files/LSTM_predict.pt").cpu()
    # 数据分割
    pulseData = np.split(pulseData,N,axis=0)

    # 转换成tensor输入模型
    pulseData = torch.tensor(pulseData, dtype=torch.float32)
    # print(pulseData.size())
    result = rnn_model(pulseData)
    #print(result)
    result = torch.unsqueeze(torch.sum(result,axis = 0),dim=0)
    _, maxIndex = torch.max(result.data, 1)
    return pulseType[maxIndex]

def mulPulsePrediction(testSize,totalSize,cursor):
    # 1 加载模型
    rnn_model = FCLSTM()
    rnn_model.load_state_dict(torch.load('./files/LSTM_predict_mul.pt', map_location='cpu'))
    rnn_model.eval()
    # 2读取测试数据 testSize个
    batch_size = N  # 设置每个批读N个
    randomList=random.sample(range(0,totalSize),testSize)
    # index = random.randint(0,totalSize-testSize)
    # tst_dataset = TestDataset(index, index+testSize,cursor)
    tst_dataset = TestDataset(randomList, cursor)
    tst_dataloader = data.DataLoader(tst_dataset, batch_size=batch_size)#, shuffle=True去除打乱否则数据不对
    # 3 全部测试集测试准确度
    correct = 0
    total = 0
    predicted=0
    labels=0
    predictedSet=[]
    labelSet=[]
    id=0
    idSet=[]
    # 对一个病人的N个数据进行统计 求出N个结果中最多的结果作为最后病人的诊断结果
    with torch.no_grad():
        for tempdata in tst_dataloader:
            pulse_data, labels, id = tempdata
            outputs = rnn_model(pulse_data)
            # 对一个病人N行6列预测值进行按行相加
            outputs = torch.unsqueeze(torch.sum(outputs, axis=0), dim=0)
            # 得到最大的值的索引
            _, predicted = torch.max(outputs.data, 1)
            # 判断是否和原标签对应
            total += labels.size(0)
            correct += (predicted == labels[0]).sum().item()
            predictedSet.append(predicted.numpy()[0])
            labelSet.append(labels.numpy()[0])
            idSet.append(id[0])
    # print(predicted[0])
    # print(labels.numpy())
    #print(predictedSet)
    #print(labelSet)
    return idSet,predictedSet,labelSet,correct,total/N,round(correct / (total/N), 4)#因为total数在裁剪过程中被分成了N份，乘了个N

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