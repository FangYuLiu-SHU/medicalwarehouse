import pandas as pd
import torch
from torch.utils import data


N = 64 #每个表分成64份每份 40个
K = 400  # history 35
L = 6  # 分类数
in_dim = 57
HIDDEN_SIZE = K
BATCH_SIZE = 64
EPOCH = 1000  # iteration times
row = 2560
col = 57
# data_num = 1009#数据量
data_num = 800#数据量

class TestDataset(data.Dataset):

    # def __init__(self,start,end,cursor):
    def __init__(self, randomList, cursor):
        # 读数据
        self.data_x, self.data_y, self.data_id = [], [], []
        lable_df = pd.read_csv('./files/df_info_merge.csv')

        #读取start到end个病人数据
        # for i in range(start,end):
        for i in randomList:
            sql = ""
            if(lable_df['id'][i][0]=='k'):
                sql = "select * from ods_kidney_pulse_" + lable_df['id'][i]
            elif(lable_df['id'][i][0]=='l'):
                sql = "select * from ods_lung_pulse_" + lable_df['id'][i]
            elif (lable_df['id'][i][0] == '2'):
                sql = "select * from ods_liver_pulse_" + lable_df['id'][i]
            print('读第'+str(i)+'个data表')
            # 从数据库获取病人脉信号表
            try:
                cursor.execute(sql)
                query_result = cursor.fetchall()
                pulse_df = pd.DataFrame(list(query_result))
                pulse_df = pulse_df.dropna(axis=1)
                # 每2560*57个数据分成n个数据并配上标签
                for j in range(N):
                    self.data_y.append(lable_df['pulse2'][i])
                    self.data_id.append(lable_df['id'][i])
                    self.data_x.append(pulse_df.loc[j * (row / N):(j + 1) * (row / N) - 1, :].values)
            except:
                print('从服务器获取数据失败')

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

