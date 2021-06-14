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
from algorithm.pulsePredictLSTM import FCLSTM

#对应关系[0,1,2,3] = [沉细，沉，细，弦]
def pulsePrediction(pulseData):
    puseType=['沉细', '沉', '细', '弦细']
    n = torch.load("./files/LSTM_predict.plt").cpu()
    pulseData = torch.from_numpy(pulseData).to(torch.float32)
    pulseData = torch.unsqueeze(pulseData, dim=0)
    result=n(pulseData)
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