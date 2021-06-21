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
from algorithm.modelLSTM import FCLSTM

#对应关系[0,1,2,3] = [沉细，沉，细，弦]
# 沉细-0 细-1 弦-2 弦细-3 滑-4 濡-5
def pulsePrediction(pulseData):
    puseType=['沉细', '细', '弦', '弦细', '滑', '濡']
    rnn_model = FCLSTM()
    rnn_model.load_state_dict(torch.load('./files/LSTM_predict.pt', map_location=torch.device('cpu') ))
    rnn_model.eval()
    # n = torch.load("./files/LSTM_predict.pt").cpu()
    pulseData = torch.from_numpy(pulseData).to(torch.float32)
    pulseData = torch.unsqueeze(pulseData, dim=0)
    result=rnn_model(pulseData)
    print(result)
    _, maxIndex = torch.max(result.data, 1)
    #print(puseType[maxIndex])
    return puseType[maxIndex]

# x = FCLSTM()
# x=""
# if cuda.is_available():
#     x = torch.zeros((2560, 56)).cuda()
# else:
#     x = torch.zeros((2560, 56))
# x=torch.unsqueeze(x, dim=0)
# y = n(x)
# print(y)
# pulsePrediction(x)