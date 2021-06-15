import logging
import sys
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from torch import cuda
from torch import nn
from torch import optim
from torch.utils import data
from algorithm.modelLSTM import FCLSTM

# 2模型输入参数加载模型
K = 90  # history 35
L = 4  # 分类数
in_dim = 57
rows = 2560
HIDDEN_SIZE = K
BATCH_SIZE = 10
EPOCH = 1000  # iteration times
# 定义数据集
class Dataset(data.Dataset):

    def __init__(self, start, end, filePath):
        # 读数据
        self.data_x, self.data_y = [], []
        list = [i for i in range(in_dim)]
        lable_df = pd.read_csv(filePath)
        #读取n个数据
        for i in range(start, end):
            self.data_y.append(lable_df['Pulse2'][i])
            pulse_df = pd.read_csv('../files/data/ods_pulse_sig_' +
                                   lable_df['User_id'][i] + '.csv',
                                   names=list, nrows=rows, usecols=[i for i in range(in_dim)])
            # 删除NaN列
            pulse_df = pulse_df.dropna(axis=1)
            self.data_x.append(pulse_df.values)
            print(i)

        # 转换数据
        self.data_x = torch.tensor(self.data_x, dtype=torch.float32)
        self.data_y = torch.tensor(self.data_y, dtype=torch.long)#标签是long类型
        # print(self.data_y)

    # 样本长度
    def __len__(self):
        return self.data_x.shape[0]

    # 取第几个数据
    def __getitem__(self, index):
        return self.data_x[index], self.data_y[index]

if __name__ == '__main__':
    # 1加载数据集
    # DATASET_PATH = sys.argv[1] + '/dmGrid3x3/'
    filePath='../files/pulse_label_merge.csv'
    sst_dataset = Dataset(0, 267, filePath)
    sst_dataloader = data.DataLoader(sst_dataset, batch_size=BATCH_SIZE, shuffle=True)
    if cuda.is_available():
        net = FCLSTM().cuda()
    else:
        net = FCLSTM()
    # 4定义损失函数和优化方法
    criterion = nn.CrossEntropyLoss()#分类采用交叉熵损失,回归使用均方差
    optimizer = optim.Adam(net.parameters(), lr=0.0001)  # 优化器
    # 5训练
    epochLoss = []
    tempLoss = 0
    for epoch in range(EPOCH):
        logging.warning(epoch)
        for x, y in sst_dataloader:
            # 加载数据
            if cuda.is_available():
                x = x.cuda()
                y = y.cuda()

            # 前向传播
            out = net(x)
            loss = criterion(out, y)
            print(f"loss {loss.item()}")
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        logging.warning(loss.data)
        epochLoss.append(loss.data.cpu().numpy())
        # 精度不再下降就结束
        # print(f"loss{loss.item()}")
        # if epoch > 32 and 0.001 > loss.data.cpu().numpy() - tempLoss > -0.001:
        #     break
        # else:
        #     tempLoss = loss.data.cpu().numpy()
    # 6保存模型
    torch.save(net, "../files/LSTM_predict.plt")
    epochLoss = pd.DataFrame(epochLoss)
    epochLoss.to_csv('../files/epochLoss.csv', header=False)