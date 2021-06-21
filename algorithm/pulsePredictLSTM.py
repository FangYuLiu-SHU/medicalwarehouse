import logging
import pandas as pd
import torch
from torch import nn, optim
from torch.utils import data
from torch import cuda
# from modelLSTM import FCLSTM
from algorithm.modelLSTM import FCLSTM

K = 90  # history 35
L = 6  # 分类数
in_dim = 57
HIDDEN_SIZE = K
BATCH_SIZE = 64
EPOCH = 1000  # iteration times
row=2560
col=57
# 定义数据集
class Dataset(data.Dataset):

    def __init__(self,start,end):
        # 读数据
        self.data_x, self.data_y, self.data_id = [], [], []
        # list = [i for i in range(57)]
        lable_df = pd.read_csv('./files/df_info_merge.csv')

        #读取n个数据
        for i in range(start,end):
            self.data_y.append(lable_df['pulse2'][i])
            self.data_id.append(lable_df['id'][i])
            if(lable_df['id'][i][0]=='k'):
                pulse_df = pd.read_csv('./files/data/ods_kidney_pulse_' +
                                       lable_df['id'][i] + '.csv',
                                       nrows=row,usecols=[i for i in range(col)])
            elif(lable_df['id'][i][0]=='l'):
                pulse_df = pd.read_csv('./files/data/ods_lung_pulse_' +
                                       lable_df['id'][i] + '.csv',
                                       nrows=row, usecols=[i for i in range(col)])
            elif (lable_df['id'][i][0] == '2'):
                pulse_df = pd.read_csv('./files/data/ods_liver_pulse_' +
                                       lable_df['id'][i] + '.csv',
                                       nrows=row, usecols=[i for i in range(col)])
            print('读第'+str(i)+'个data表')
            # 删除NaN列
            pulse_df = pulse_df.dropna(axis=1)
            self.data_x.append(pulse_df.values)

        # 转换数据
        self.data_x = torch.tensor(self.data_x, dtype=torch.float32)
        self.data_y = torch.tensor(self.data_y, dtype=torch.long)#标签是long类型
        # print(self.data_y)

    # 样本长度
    def __len__(self):
        return self.data_x.shape[0]

    # 取第几个数据
    def __getitem__(self, index):
        return self.data_x[index], self.data_y[index],self.data_id[index]


# epochLoss = pd.DataFrame(epochLoss)
# epochLoss.to_csv(BASE_PATH + sys.argv[1] + 'DmFCLSTM' + sys.argv[2] + '-' + sys.argv[3] + '-epochLoss.csv',header=False)

# # 读数据
# truth_y = []
# pred_y = []
#
#
# test_x, test_y = [], []
# list = [i for i in range(60)]
# lable_df = pd.read_csv('labels.csv')
# for i in range(201,len(lable_df)):
#     test_y.append(lable_df['Pulse2'][i])
#     pulse_df = pd.read_csv(r'E:\WorkSpace\AllWorkspaces\Pycharmworkspace\medicalwarehouse\data\ods_pulse_sig_' +
#                            lable_df['User_id'][i] + '.csv',
#                            names=list,nrows=2560)
#     pulse_df = pulse_df.dropna(axis=1)
#     test_x.append(pulse_df.values)
# # for P in Points:
# #     sst = pd.read_csv(BASE_PATH + DATASET_PATH + str(P) + '.csv', header=None)
# #     test_x, test_y = [], []
# #     for i in range(1792, 2192 - K - L):
# #         test_x.append(sst.values[i:i + K, 0])
# #         test_y.append(sst.values[i + K:i + K + L, 0])
#
#     # 转化数据
#     test_x = torch.tensor(test_x, dtype=torch.float32)
#     truth_y.append(test_y)
#
#     # 测试
#     net = net.eval()
#     if cuda.is_available():
#         test_x = test_x.cuda()
#         pred_y.append(net(test_x).cpu().data.numpy())
#     else:
#         pred_y.append(net(test_x).data.numpy())
# truth_y = np.array(truth_y)
# pred_y = np.array(pred_y)
# truth_y = truth_y.reshape(-1, L)
# pred_y = pred_y.reshape(-1, L)
#
# # 计算性能
# test_loss = pd.read_csv(BASE_PATH + sys.argv[1] + 'DmGrid.csv', index_col=0, header=None)
# test_loss.loc[sys.argv[1] + 'DmGridFCLSTM' + sys.argv[2] + '-' + sys.argv[3]] = [sys.argv[2], sys.argv[3],
#                                                                                  mean_squared_error(truth_y, pred_y),
#                                                                                  mean_absolute_error(truth_y, pred_y),
#                                                                                  r2_score(truth_y, pred_y)]
# test_loss.to_csv(BASE_PATH + sys.argv[1] + 'DmGrid.csv', header=False)

if __name__ == '__main__':
    # 1加载数据集
    # DATASET_PATH = sys.argv[1] + '/dmGrid3x3/'
    sst_dataset = Dataset(0, 857)
    sst_dataloader = data.DataLoader(sst_dataset, batch_size=BATCH_SIZE, shuffle=True)

    # 2模型输入参数加载模型
    if cuda.is_available():
        print('gpu is ok')
        net = FCLSTM().cuda()
    else:
        net = FCLSTM()
    # 4定义损失函数和优化方法
    criterion = nn.CrossEntropyLoss()#分类采用交叉熵损失,回归使用均方差
    # optimizer = optim.Adam(net.parameters(), lr=0.0001,weight_decay=5)  # 优化器 学习率 + L2正则
    optimizer = optim.Adam(net.parameters(), lr=0.0005)  # 优化器 学习率 + L2正则
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
    # 6保存模型
    # torch.save(net, "LSTM_predict.plt")

    torch.save(net.state_dict(), './files/LSTM_predict.pt')
    print('模型参数保存成功！')
