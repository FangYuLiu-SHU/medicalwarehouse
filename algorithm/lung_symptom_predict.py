#使用svm对肾表的症状进行二分类
# 导入第三方模块
import numpy as np
from imblearn.over_sampling import SMOTE
from sklearn import svm
import joblib
from sklearn import model_selection
from sklearn import metrics
import pandas as pd
import re
import random

def lung_tongue_pulse_code(df_lung):
    # 对脉的标签描述进行清洗
    df_lung['pulse0'] = df_lung['pulse'].str.replace("偏", "")
    df_lung['pulse0'] = df_lung['pulse0'].str.replace("右", "")
    df_lung['pulse0'] = df_lung['pulse0'].str.replace("左", "")
    df_lung['pulse0'] = df_lung['pulse0'].str.replace("脉", "")
    df_lung['pulse0'] = df_lung['pulse0'].str.replace("\r", "")
    df_lung['pulse0'] = df_lung['pulse0'].str.strip()
    df_lung = df_lung[~df_lung['pulse0'].isin([""])]
    # df_lung['pulse1'] = df_lung['pulse0'].str[0]
    # 对脉的标签描述进行编码
    # 其他-0 滑-1 细-2 弦-3
    # 其它默认0
    df_lung['pulse2'] = 0
    pat0 = '滑.*'
    df_lung.loc[~df_lung['pulse0'].apply(lambda x: re.match(pat0, x)).isna(), 'pulse2'] = 1
    pat1 = '细.*'
    df_lung.loc[~df_lung['pulse0'].apply(lambda x: re.match(pat1, x)).isna(), 'pulse2'] = 2
    pat2 = '弦.*'
    df_lung.loc[~df_lung['pulse0'].apply(lambda x: re.match(pat2, x)).isna(), 'pulse2'] = 3

    # 对舌的标签描述进行编码
    df_lung['tongue_proper_color'] = 0  # 舌质颜色 淡红（正常）-0 淡白-1 红-2 暗/紫-3
    df_lung['tongue_proper_shape_pang'] = 0  # 舌质形态 正常-0 胖-1    裂纹(太少不用)  嫩 胖 齿印
    # df_lung['tongue_proper_shape_neng'] = 0  # 舌质形态 正常-0  嫩-1  只有一例特征舍去
    df_lung['tongue_proper_shape_chiyin'] = 0  # 舌质形态 正常-0  齿印-1
    df_lung['tongue_moss_color'] = 0  # 苔色白（正常）-0、黄-1
    df_lung['tongue_moss_nature'] = 0  # 苔质 薄（正常）-0  少-1  腻-2 厚（4个样本不用了）薄少和润滑（不用）燥糙和腐腻
    # 舌色编码
    patt0 = r'.*淡(?!红).*'
    df_lung.loc[~df_lung['tongue'].apply(lambda x: re.match(patt0, str(x))).isna(), 'tongue_proper_color'] = 1
    patt1 = r'.*[^淡]红.*'
    df_lung.loc[~df_lung['tongue'].apply(lambda x: re.match(patt1, x)).isna(), 'tongue_proper_color'] = 2
    df_lung.loc[df_lung['tongue'].str.contains('暗'), 'tongue_proper_color'] = 3
    df_lung.loc[df_lung['tongue'].str.contains('紫'), 'tongue_proper_color'] = 3
    # 舌形编码
    df_lung.loc[df_lung['tongue'].str.contains('胖'), 'tongue_proper_shape_pang'] = 1
    # df_lung.loc[df_lung['tongue'].str.contains('嫩'), 'tongue_proper_shape_neng'] = 1
    df_lung.loc[df_lung['tongue'].str.contains('齿'), 'tongue_proper_shape_chiyin'] = 1
    # 苔色编码
    df_lung.loc[df_lung['tongue'].str.contains('黄'), 'tongue_moss_color'] = 1
    # 苔质编码
    df_lung.loc[df_lung['tongue'].str.contains('少'), 'tongue_moss_nature'] = 1
    df_lung.loc[df_lung['tongue'].str.contains('腻'), 'tongue_moss_nature'] = 2

    # 对西医诊断进行编码
    df_lung['wm_diagnosis_code'] = 0
    pat0 = '.*咳嗽.*'
    df_lung.loc[~df_lung['Wesmedicine_diagnosis'].apply(lambda x: re.match(pat0, x)).isna(), 'wm_diagnosis_code'] = 1
    pat1 = '.*支气管.*'
    df_lung.loc[~df_lung['Wesmedicine_diagnosis'].apply(lambda x: re.match(pat1, x)).isna(), 'wm_diagnosis_code'] = 2

    return df_lung


def process_data():
    # 读取数据
    df_lung = pd.read_csv('../files/dwd_lung_info.csv')
    # 清洗下
    df_lung['PEF'] = df_lung['PEF'].astype(str).str.replace(',', '.')
    df_lung['PEF'] = df_lung['PEF'].astype(float)
    # df_lung['FEV1/FVC'] = df_lung['FEV1/FVC'].astype(float)
    df_lung.dropna(inplace=True)
    # 获得编码
    df_lung = lung_tongue_pulse_code(df_lung)

    kidney_qi_deficiency = df_lung['kidney_qi_deficiency']
    spleen_qi_deficiency = df_lung['spleen_qi_deficiency']
    Lung_qi_deficiency = df_lung['Lung_qi_deficiency']

    # 删除不需要的列
    df_lung.drop(
        ['id', 'Wesmedicine_diagnosis', 'tongue', 'pulse', 'pulse0', 'Lung_qi_deficiency', 'spleen_qi_deficiency',
         'kidney_qi_deficiency'], inplace=True, axis=1)
    # 把标签3个Y移到第一列方便操作
    df_lung.insert(0, 'kidney_qi_deficiency', kidney_qi_deficiency)
    df_lung.insert(0, 'spleen_qi_deficiency', spleen_qi_deficiency)
    df_lung.insert(0, 'Lung_qi_deficiency', Lung_qi_deficiency)
    # 修改名称
    df_lung.rename(columns={'pulse2': 'pulse'}, inplace=True)

    # 将数值型的sex，pulse，tongue_proper_color，tongue_moss_nature转换为类别型，否则无法对其哑变量处理
    df_lung.sex = df_lung.sex.astype('category')
    df_lung.pulse = df_lung.pulse.astype('category')
    df_lung.tongue_proper_color = df_lung.tongue_proper_color.astype('category')
    df_lung.tongue_moss_nature = df_lung.tongue_moss_nature.astype('category')
    df_lung.wm_diagnosis_code = df_lung.wm_diagnosis_code.astype('category')

    df_lung.tongue_proper_shape_pang = df_lung.tongue_proper_shape_pang.astype('category')
    df_lung.tongue_proper_shape_chiyin = df_lung.tongue_proper_shape_chiyin.astype('category')
    df_lung.tongue_moss_color = df_lung.tongue_moss_color.astype('category')

    # 哑变量处理
    dummy = pd.get_dummies(df_lung[['sex', 'pulse', 'tongue_proper_color', 'tongue_moss_nature', 'wm_diagnosis_code']])
    df_lung.drop(['sex', 'pulse', 'tongue_proper_color', 'tongue_moss_nature', 'wm_diagnosis_code'], inplace=True,
                 axis=1)

    df_lung = pd.concat([df_lung, dummy], axis=1)
    # df_lung.to_csv('df_lung.csv')
    return df_lung


def train_model_lung(df_lung):
    # 模型1 肺气虚
    # 由于数据集分布不均衡使用SMOTE进行过采样 原Counter({1: 410, 0: 56})
    X = df_lung.iloc[:, 3:]
    Y = df_lung.Lung_qi_deficiency
    # 定义SMOTE模型，random_state相当于随机数种子的作用
    smo = SMOTE(random_state=0)
    X_smo, Y_smo = smo.fit_resample(X, Y)
    df_lung = pd.concat([Y_smo, X_smo], axis=1)
    # 删除空值 现在 Counter({2: 173, 1: 173})
    df_lung.dropna(inplace=True)

    # 将数据拆分为训练集和测试集

    X_train, X_test, y_train, y_test = model_selection.train_test_split(df_lung.iloc[:, 1:], df_lung.Lung_qi_deficiency,
                                                                        test_size=0.25, random_state=1234)

    # print(df_lung.Lung_qi_deficiency)
    # print(df_lung.iloc[:, 1:])
    # 选择线性可分SVM模型
    linear_svc = svm.LinearSVC(max_iter=100000000)
    # 模型在训练数据集上的拟合
    linear_svc.fit(X_train, y_train)
    # 模型在测试集上的预测
    y_pred = linear_svc.predict(X_test)
    # 模型的预测精度P，召回率R，F1值
    accuracy = metrics.accuracy_score(y_test, y_pred)
    precision = metrics.precision_score(y_test, y_pred)
    f1_socre = metrics.f1_score(y_test, y_pred)
    print('accuracy:{},precision:{},f1_socre:{}'.format(accuracy, precision, f1_socre))
    # 保存模型
    joblib.dump(linear_svc, '../files/SVM_lung_lung_predict.pkl')


def train_model_spleen(df_lung):
    # 模型2 脾气虚
    # 由于数据集分布不均衡使用SMOTE进行过采样 原Counter({0: 378, 1: 88})
    X = df_lung.iloc[:, 3:]
    Y = df_lung.spleen_qi_deficiency
    # 定义SMOTE模型，random_state相当于随机数种子的作用
    smo = SMOTE(random_state=0)
    X_smo, Y_smo = smo.fit_resample(X, Y)
    df_lung = pd.concat([Y_smo, X_smo], axis=1)
    # 删除空值 现在 Counter({2: 173, 1: 173})
    df_lung.dropna(inplace=True)

    X_train, X_test, y_train, y_test = model_selection.train_test_split(df_lung.iloc[:, 1:],
                                                                        df_lung.spleen_qi_deficiency,
                                                                        test_size=0.25, random_state=1234)
    # 选择线性可分SVM模型
    linear_svc = svm.LinearSVC(max_iter=100000000)
    # 模型在训练数据集上的拟合
    linear_svc.fit(X_train, y_train)
    # 模型在测试集上的预测
    y_pred = linear_svc.predict(X_test)
    # 模型的预测精度P，召回率R，F1值
    accuracy = metrics.accuracy_score(y_test, y_pred)
    precision = metrics.precision_score(y_test, y_pred)
    f1_socre = metrics.f1_score(y_test, y_pred)
    print('accuracy:{},precision:{},f1_socre:{}'.format(accuracy, precision, f1_socre))

    # 保存模型
    joblib.dump(linear_svc, '../files/SVM_lung_spleen_predict.pkl')


def train_model_kidney(df_lung):
    # 模型3 肾气虚

    # 由于数据集分布不均衡使用SMOTE进行过采样 原Counter({0: 414, 1: 52})
    X = df_lung.iloc[:, 3:]
    Y = df_lung.kidney_qi_deficiency
    # 定义SMOTE模型，random_state相当于随机数种子的作用
    smo = SMOTE(random_state=0)
    X_smo, Y_smo = smo.fit_resample(X, Y)
    df_lung = pd.concat([Y_smo, X_smo], axis=1)
    # 删除空值 现在 Counter({2: 173, 1: 173})
    df_lung.dropna(inplace=True)

    X_train, X_test, y_train, y_test = model_selection.train_test_split(df_lung.iloc[:, 1:],
                                                                        df_lung.kidney_qi_deficiency,
                                                                        test_size=0.25, random_state=1234)
    # 选择线性可分SVM模型
    linear_svc = svm.LinearSVC(max_iter=100000000)
    # 模型在训练数据集上的拟合
    linear_svc.fit(X_train, y_train)
    # 模型在测试集上的预测
    y_pred = linear_svc.predict(X_test)
    # 模型的预测精度P，召回率R，F1值
    accuracy = metrics.accuracy_score(y_test, y_pred)
    precision = metrics.precision_score(y_test, y_pred)
    f1_socre = metrics.f1_score(y_test, y_pred)
    print('accuracy:{},precision:{},f1_socre:{}'.format(accuracy, precision, f1_socre))
    # 保存模型
    joblib.dump(linear_svc, '../files/SVM_lung_kidney_predict.pkl')


def sigle_predict(dict):
    # 加载模型
    model_lung = joblib.load('./files/SVM_lung_lung_predict.pkl')
    model_spleen = joblib.load('./files/SVM_lung_spleen_predict.pkl')
    model_kidney = joblib.load('./files/SVM_lung_kidney_predict.pkl')

    # 输入示例dict1 = {'sex': '1', 'userage': '45','wd':'咳嗽', 'FEV1': 1.07,'FVC':1.83,'FEV1%':42.29,'FEV1/FVC':0.584699454,'PEF':1.22,'Tou': '舌红苔少',
    #          'pulseType': '脉滑'}
    df_sig_lung = pd.DataFrame(dict, index=[0])
    # 重命名
    df_sig_lung.columns = ['sex', 'age', 'Wesmedicine_diagnosis', 'FEV1', 'FVC', 'FEV1%', 'FEV1/FVC', 'PEF', 'tongue', 'pulse']
    # 脉清洗
    df_sig_lung['pulse0'] = df_sig_lung['pulse'].str.replace("偏", "").str.replace("右", "").str.replace("左",
                                                                                                       "").str.replace(
        "脉", "").str.replace("\r", "").str.strip()
    # 脉编码
    df_sig_lung['pulse2'] = 0
    pat0 = '滑.*'
    df_sig_lung.loc[~df_sig_lung['pulse0'].apply(lambda x: re.match(pat0, x)).isna(), 'pulse2'] = 1
    pat1 = '细.*'
    df_sig_lung.loc[~df_sig_lung['pulse0'].apply(lambda x: re.match(pat1, x)).isna(), 'pulse2'] = 2
    pat2 = '弦.*'
    df_sig_lung.loc[~df_sig_lung['pulse0'].apply(lambda x: re.match(pat2, x)).isna(), 'pulse2'] = 3

    # 对舌的标签描述进行编码
    df_sig_lung['tongue_proper_color'] = 0  # 舌质颜色 淡红（正常）-0 淡白-1 红-2 暗/紫-3
    df_sig_lung['tongue_proper_shape_pang'] = 0  # 舌质形态 正常-0 胖-1    裂纹(太少不用)  嫩 胖 齿印
    # df_sig_lung['tongue_proper_shape_neng'] = 0  # 舌质形态 正常-0  嫩-1
    df_sig_lung['tongue_proper_shape_chiyin'] = 0  # 舌质形态 正常-0  齿印-1
    df_sig_lung['tongue_moss_color'] = 0  # 苔色白（正常）-0、黄-1
    df_sig_lung['tongue_moss_nature'] = 0  # 苔质 薄（正常）-0  少-1  腻-2 厚（4个样本不用了）薄少和润滑（不用）燥糙和腐腻
    # 舌色编码
    patt0 = r'.*淡(?!红).*'
    df_sig_lung.loc[~df_sig_lung['tongue'].apply(lambda x: re.match(patt0, str(x))).isna(), 'tongue_proper_color'] = 1
    patt1 = r'.*[^淡]红.*'
    df_sig_lung.loc[~df_sig_lung['tongue'].apply(lambda x: re.match(patt1, str(x))).isna(), 'tongue_proper_color'] = 2
    df_sig_lung.loc[df_sig_lung['tongue'].str.contains('暗'), 'tongue_proper_color'] = 3
    df_sig_lung.loc[df_sig_lung['tongue'].str.contains('紫'), 'tongue_proper_color'] = 3
    # 舌形编码
    df_sig_lung.loc[df_sig_lung['tongue'].str.contains('胖'), 'tongue_proper_shape_pang'] = 1
    # df_sig_lung.loc[df_sig_lung['tongue'].str.contains('嫩'), 'tongue_proper_shape_neng'] = 1
    df_sig_lung.loc[df_sig_lung['tongue'].str.contains('齿'), 'tongue_proper_shape_chiyin'] = 1
    # 苔色编码
    df_sig_lung.loc[df_sig_lung['tongue'].str.contains('黄'), 'tongue_moss_color'] = 1
    # 苔质编码
    df_sig_lung.loc[df_sig_lung['tongue'].str.contains('少'), 'tongue_moss_nature'] = 1
    df_sig_lung.loc[df_sig_lung['tongue'].str.contains('腻'), 'tongue_moss_nature'] = 2

    # 诊断编码
    # 对西医诊断进行编码
    df_sig_lung['wm_diagnosis_code'] = 0
    pat0 = '.*咳嗽.*'
    df_sig_lung.loc[~df_sig_lung['Wesmedicine_diagnosis'].apply(lambda x: re.match(pat0, x)).isna(), 'wm_diagnosis_code'] = 1
    pat1 = '.*支气管.*'
    df_sig_lung.loc[~df_sig_lung['Wesmedicine_diagnosis'].apply(lambda x: re.match(pat1, x)).isna(), 'wm_diagnosis_code'] = 2

    # 删除源列
    df_sig_lung.drop(['tongue', 'pulse', 'pulse0', 'Wesmedicine_diagnosis'], inplace=True, axis=1)
    df_sig_lung.rename(columns={'pulse2': 'pulse'}, inplace=True)

    # 转化成one-hot
    from pandas.api.types import CategoricalDtype
    df_sig_lung.sex = df_sig_lung.sex.astype(CategoricalDtype(categories=["1", "2"], ordered=True))
    df_sig_lung['pulse'] = df_sig_lung['pulse'].astype(CategoricalDtype(categories=[0, 1, 2, 3], ordered=True))
    df_sig_lung['tongue_proper_color'] = df_sig_lung['tongue_proper_color'].astype(
        CategoricalDtype(categories=[0, 1, 2, 3], ordered=True))
    df_sig_lung['tongue_moss_nature'] = df_sig_lung['tongue_moss_nature'].astype(
        CategoricalDtype(categories=[0, 1, 2], ordered=True))
    df_sig_lung['wm_diagnosis_code'] = df_sig_lung['wm_diagnosis_code'].astype(
        CategoricalDtype(categories=[0, 1, 2], ordered=True))
    df_sig_lung = pd.get_dummies(df_sig_lung, columns=['sex', 'pulse', 'tongue_proper_color', 'tongue_moss_nature',
                                                       'wm_diagnosis_code'], prefix_sep='_', dummy_na=False,
                                 drop_first=False)
    # df_sig_lung.to_csv('../files/df_sig_lung.csv',index=False)
    # 测试的单数据格式如下array([[1,2,3,4]])

    classification_lung = model_lung.predict(df_sig_lung.values)
    classification_spleen = model_spleen.predict(df_sig_lung.values)
    classification_kidney = model_kidney.predict(df_sig_lung.values)
    # print(classification_lung,classification_spleen,classification_kidney)
    # 分别对应是/否(1/0)有肺气虚，脾气虚，肾气虚
    result = np.append(classification_lung, classification_spleen)
    result = np.append(result, classification_kidney)
    # print(result)
    return result

def multi_predict(num,cursor):
    Type1 = ['无肺气虚', '有肺气虚']
    Type2 = ['无脾气虚', '有脾气虚']
    Type3 = ['无肾气虚', '有肾气虚']
    # 读取数据，随机选择num个样本进行验证
    # 改成读数据库，随机挑选的样本，应该是判断有脉象表格的，过滤空cell值
    # sql = "select * from dwd_lung_info"
    sql = "select * from dwd_lung_info where trim(id) != '' and trim(sex) != '' and trim(age) != '' and trim(Wesmedicine_diagnosis) != '' and trim(Lung_qi_deficiency) != '' and trim(spleen_qi_deficiency) != '' and trim(kidney_qi_deficiency) != '' and trim(FEV1) != '' and trim(FVC) != '' and trim(`FEV1%`) != '' and trim(FEV1/FVC) != '' and trim(PEF) != '' and trim(tongue) != '' and trim(pulse) != ''"
    cursor.execute(sql)  # 获得所有符合条件的数据
    dataSet = cursor.fetchall()
    set = np.array(dataSet)
    indexs = random.sample(range(0, set.shape[0]), num)

    idSet=[]
    predictType1=[]
    predictType2 = []
    predictType3 = []
    labelType1 = []
    labelType2 = []
    labelType3 = []
    correct1 = 0
    correct2 = 0
    correct3 = 0
    total = num
    tempParms={'sex': '1', 'userage': '75','Wesmedicine_diagnosis':'咳嗽', 'FEV1': '2.2','FVC':'2.71','FEV1%':'83.33','FEV1/FVC':'0.811808118','PEF':'4.02','Tou': '苔黄', 'pulseType': '脉弦滑'}
    # tempParms = {'sex': '2', 'userage': '65', 'ALTD': '30', 'Tou': '舌苔黄腻', 'pulseType': '弦数'}
    for index in indexs:
        idSet.append(str(set[index, 0]))
        tempParms['sex']=str(set[index,1])
        tempParms['userage']=str(set[index,2])
        tempParms['Wesmedicine_diagnosis'] = str(set[index, 3])
        tempParms['FEV1']=str(set[index,7])
        tempParms['FVC'] = str(set[index, 8])
        tempParms['FEV1%'] = str(set[index, 9])
        tempParms['FEV1/FVC'] = str(set[index, 10])
        tempParms['PEF'] = str(set[index, 11]).replace(',', '.')
        tempParms['Tou']=set[index,12]
        tempParms['pulseType']=set[index,13]
        temp = sigle_predict(tempParms)
        predictIndex1 = int(temp[0])
        predictIndex2 = int(temp[1])
        predictIndex3 = int(temp[2])
        #第4列数据没用上
        labelIndex1 = int(set[index, 4])
        labelIndex2 = int(set[index, 5])
        labelIndex3 = int(set[index, 6])
        predictType1.append(Type1[predictIndex1])
        predictType2.append(Type2[predictIndex2])
        predictType3.append(Type3[predictIndex3])
        labelType1.append(Type1[labelIndex1])
        labelType2.append(Type2[labelIndex2])
        labelType3.append(Type3[labelIndex3])
        if(predictIndex1 == labelIndex1):
            correct1 += 1
        if (predictIndex2 == labelIndex2):
            correct2 += 1
        if (predictIndex3 == labelIndex3):
            correct3 += 1
        x=[]
        x.append(labelIndex1)
        x.append(labelIndex2)
        x.append(labelIndex3)
    accuracy1 = round(correct1 / total, 3)
    accuracy2 = round(correct2 / total, 3)
    accuracy3 = round(correct3 / total, 3)
    return idSet,predictType1,predictType2,predictType3,labelType1,labelType2,labelType3,correct1,correct2,correct3,total,accuracy1,accuracy2,accuracy3

# if __name__ == '__main__':
#     df_lung = process_data()
#     print(df_lung.shape)
#     train_model_lung(df_lung)
#     print(df_lung.shape)
#     train_model_kidney(df_lung)
#     print(df_lung.shape)
#     train_model_spleen(df_lung)
#     print(df_lung.shape)
#     # 111
#     dict1 = {'sex': '2', 'userage': '51','wm_diagnosis':'咳嗽' , 'FEV1': 2.49,'FVC':3.15,'FEV1%':74.55,'FEV1/FVC':0.79047619,'PEF':5.97,'Tou': '舌淡苔白',
#              'pulseType': '脉细'}
#     # 011
#     # dict1 = {'sex': '2', 'userage': '50', 'FEV1': 1.65,'FVC':1.76,'FEV1%':91.67,'FEV1/FVC':0.9375,'PEF':2.38,'Tou': '舌淡苔白',
#     #          'pulseType': '脉细'}
#     # 000
#     # dict1 = {'sex': '1', 'userage': '75', 'FEV1': '2.2','FVC':'2.71','FEV1%':'83.33','FEV1/FVC':'0.811808118','PEF':'4.02','Tou': '苔黄',
#     #          'pulseType': '脉弦滑'}
#     x=sigle_predict(dict1)[0]
#     print(x)