#使用svm对肾表的症状进行二分类
# 导入第三方模块
from sklearn import svm
import joblib
from sklearn import model_selection
from sklearn import metrics
import pandas as pd
import re
from imblearn.over_sampling import SMOTE
import random
import numpy as np

def kidney_tongue_pulse_code(df_kidney):
    # 对脉的标签描述进行清洗
    df_kidney['pulse0'] = df_kidney['pulse'].str.replace("偏", "")
    df_kidney['pulse0'] = df_kidney['pulse0'].str.replace("右", "")
    df_kidney['pulse0'] = df_kidney['pulse0'].str.replace("左", "")
    df_kidney['pulse0'] = df_kidney['pulse0'].str.replace("脉", "")
    df_kidney['pulse0'] = df_kidney['pulse0'].str.replace("\r", "")
    df_kidney['pulse0'] = df_kidney['pulse0'].str.strip()
    df_kidney = df_kidney[~df_kidney['pulse0'].isin([""])]
    # 对脉的标签描述进行编码
    # 其他-0 沉-1 细-2 弦-3
    # 其它默认0
    df_kidney['pulse2'] = 0
    pat0 = '沉.*'
    df_kidney.loc[~df_kidney['pulse0'].apply(lambda x: re.match(pat0, x)).isna(), 'pulse2'] = 1
    pat1 = '细.*'
    df_kidney.loc[~df_kidney['pulse0'].apply(lambda x: re.match(pat1, x)).isna(), 'pulse2'] = 2
    pat2 = '弦.*'
    df_kidney.loc[~df_kidney['pulse0'].apply(lambda x: re.match(pat2, x)).isna(), 'pulse2'] = 3

    # 对舌的标签描述进行编码
    df_kidney['tongue_proper_color'] = 0  # 舌质颜色 淡红（正常）-0 淡白-1 红-2 暗/紫-3
    df_kidney['tongue_proper_shape_pang'] = 0  # 舌质形态 正常-0 胖-1    裂纹(太少不用)  嫩 胖 齿印
    df_kidney['tongue_proper_shape_neng'] = 0  # 舌质形态 正常-0  嫩-1
    df_kidney['tongue_proper_shape_chiyin'] = 0  # 舌质形态 正常-0  齿印-1
    df_kidney['tongue_moss_color'] = 0  # 苔色白（正常）-0、黄-1
    df_kidney['tongue_moss_nature'] = 0  # 苔质 薄（正常）-0  少-1  腻-2 厚（4个样本不用了）薄少和润滑（不用）燥糙和腐腻
    # 舌色编码
    patt0 = r'.*淡(?!红).*'
    df_kidney.loc[~df_kidney['tongue'].apply(lambda x: re.match(patt0, x)).isna(), 'tongue_proper_color'] = 1
    patt1 = r'.*[^淡]红.*'
    df_kidney.loc[~df_kidney['tongue'].apply(lambda x: re.match(patt1, x)).isna(), 'tongue_proper_color'] = 2
    df_kidney.loc[df_kidney['tongue'].str.contains('暗'), 'tongue_proper_color'] = 3
    df_kidney.loc[df_kidney['tongue'].str.contains('紫'), 'tongue_proper_color'] = 3
    # 舌形编码
    df_kidney.loc[df_kidney['tongue'].str.contains('胖'), 'tongue_proper_shape_pang'] = 1
    df_kidney.loc[df_kidney['tongue'].str.contains('嫩'), 'tongue_proper_shape_neng'] = 1
    df_kidney.loc[df_kidney['tongue'].str.contains('齿'), 'tongue_proper_shape_chiyin'] = 1
    # 苔色编码
    df_kidney.loc[df_kidney['tongue'].str.contains('黄'), 'tongue_moss_color'] = 1
    # 苔质编码
    df_kidney.loc[df_kidney['tongue'].str.contains('少'), 'tongue_moss_nature'] = 1
    df_kidney.loc[df_kidney['tongue'].str.contains('腻'), 'tongue_moss_nature'] = 2
    return df_kidney

def process_data():
    # 读取数据
    df_kidney = pd.read_csv('./files/dwd_kidney_info.csv')
    # 获得编码
    df_kidney = kidney_tongue_pulse_code(df_kidney)
    # 拼接
    # df_kidney = pd.concat([df_kidney, df], axis=1)

    symptoms_type = df_kidney['symptoms_type']
    # 删除不需要的列
    df_kidney.drop(['id', 'tongue', 'pulse', 'pulse0', 'symptoms_type'], inplace=True, axis=1)
    # 把标签Y移到第一列方便操作
    df_kidney.insert(0, 'symptoms_type', symptoms_type)
    # 修改名称
    df_kidney.rename(columns={'pulse2': 'pulse'}, inplace=True)

    # 将数值型的sex，pulse，tongue_proper_color转换为类别型，否则无法对其哑变量处理
    df_kidney.sex = df_kidney.sex.astype('category')
    df_kidney.pulse = df_kidney.pulse.astype('category')
    df_kidney.tongue_proper_color = df_kidney.tongue_proper_color.astype('category')
    df_kidney.tongue_moss_nature = df_kidney.tongue_moss_nature.astype('category')

    df_kidney.tongue_proper_shape_pang = df_kidney.tongue_proper_shape_pang.astype('category')
    df_kidney.tongue_proper_shape_neng = df_kidney.tongue_proper_shape_neng.astype('category')
    df_kidney.tongue_proper_shape_chiyin = df_kidney.tongue_proper_shape_chiyin.astype('category')
    df_kidney.tongue_moss_color = df_kidney.tongue_moss_color.astype('category')

    # 哑变量处理
    dummy = pd.get_dummies(df_kidney[['sex', 'pulse', 'tongue_proper_color','tongue_moss_nature']])
    df_kidney.drop(['sex', 'pulse','tongue_proper_color' ,'tongue_moss_nature'], inplace=True, axis=1)

    df_kidney = pd.concat([df_kidney, dummy], axis=1)
    # 由于数据集分布不均衡使用SMOTE进行过采样 原Counter({1: 367, 2: 199})
    X = df_kidney.iloc[:, 1:]
    Y = df_kidney.symptoms_type
    # 定义SMOTE模型，random_state相当于随机数种子的作用
    smo = SMOTE(random_state=0)
    X_smo, Y_smo = smo.fit_resample(X, Y)
    df_kidney = pd.concat([Y_smo, X_smo], axis=1)
    # 删除空值 现在 Counter({1: 367, 2: 300})
    df_kidney.dropna(inplace=True)
    # print(df_kidney.dtypes)
    return df_kidney

def train_model(df_kidney):

    # 将数据拆分为训练集和测试集
    X_train, X_test, y_train, y_test = model_selection.train_test_split(df_kidney.iloc[:, 1:], df_kidney.symptoms_type,
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
    f1_socre  = metrics.f1_score(y_test, y_pred)
    print('accuracy:{},precision:{},f1_socre:{}'.format(accuracy,precision,f1_socre))
    # print(y_pred)
    # print(np.array(y_train.tolist()))
    # 保存模型
    joblib.dump(linear_svc, './files/SVM_kidney_predict.pkl')


def sigle_predict(dict):
    # 加载模型
    model = joblib.load('./files/SVM_kidney_predict.pkl')

    #dict1 = {'sex': '2', 'userage': '59', 'bloodCreatinine': '110.5', 'egfr': '77.48463620335353','Tou':'舌淡齿痕苔腻', 'pulseType': '细'}
    df_sig_kidney = pd.DataFrame(dict, index=[0])
    # 重命名
    df_sig_kidney.columns = ['sex', 'age', 'serum_creatinine', 'eGFR', 'tongue', 'pulse']
    # 脉清洗
    df_sig_kidney['pulse0'] = df_sig_kidney['pulse'].str.replace("偏", "").str.replace("右", "").str.replace("左", "").str.replace("脉", "").str.replace("\r", "").str.strip()
    # 脉编码
    df_sig_kidney['pulse2'] = 0
    pat0 = '沉.*'
    df_sig_kidney.loc[~df_sig_kidney['pulse0'].apply(lambda x: re.match(pat0, x)).isna(), 'pulse2'] = 1
    pat1 = '细.*'
    df_sig_kidney.loc[~df_sig_kidney['pulse0'].apply(lambda x: re.match(pat1, x)).isna(), 'pulse2'] = 2
    pat2 = '弦.*'
    df_sig_kidney.loc[~df_sig_kidney['pulse0'].apply(lambda x: re.match(pat2, x)).isna(), 'pulse2'] = 3

    # 对舌的标签描述进行编码
    df_sig_kidney['tongue_proper_color'] = 0  # 舌质颜色 淡红（正常）-0 淡白-1 红-2 暗/紫-3
    df_sig_kidney['tongue_proper_shape_pang'] = 0  # 舌质形态 正常-0 胖-1    裂纹(太少不用)  嫩 胖 齿印
    df_sig_kidney['tongue_proper_shape_neng'] = 0  # 舌质形态 正常-0  嫩-1
    df_sig_kidney['tongue_proper_shape_chiyin'] = 0  # 舌质形态 正常-0  齿印-1
    df_sig_kidney['tongue_moss_color'] = 0  # 苔色白（正常）-0、黄-1
    df_sig_kidney['tongue_moss_nature'] = 0  # 苔质 薄（正常）-0  少-1  腻-2 厚（4个样本不用了）薄少和润滑（不用）燥糙和腐腻
    # 舌色编码
    patt0 = r'.*淡(?!红).*'
    df_sig_kidney.loc[~df_sig_kidney['tongue'].apply(lambda x: re.match(patt0, x)).isna(), 'tongue_proper_color'] = 1
    patt1 = r'.*[^淡]红.*'
    df_sig_kidney.loc[~df_sig_kidney['tongue'].apply(lambda x: re.match(patt1, x)).isna(), 'tongue_proper_color'] = 2
    df_sig_kidney.loc[df_sig_kidney['tongue'].str.contains('暗'), 'tongue_proper_color'] = 3
    df_sig_kidney.loc[df_sig_kidney['tongue'].str.contains('紫'), 'tongue_proper_color'] = 3
    # 舌形编码
    df_sig_kidney.loc[df_sig_kidney['tongue'].str.contains('胖'), 'tongue_proper_shape_pang'] = 1
    df_sig_kidney.loc[df_sig_kidney['tongue'].str.contains('嫩'), 'tongue_proper_shape_neng'] = 1
    df_sig_kidney.loc[df_sig_kidney['tongue'].str.contains('齿'), 'tongue_proper_shape_chiyin'] = 1
    # 苔色编码
    df_sig_kidney.loc[df_sig_kidney['tongue'].str.contains('黄'), 'tongue_moss_color'] = 1
    # 苔质编码
    df_sig_kidney.loc[df_sig_kidney['tongue'].str.contains('少'), 'tongue_moss_nature'] = 1
    df_sig_kidney.loc[df_sig_kidney['tongue'].str.contains('腻'), 'tongue_moss_nature'] = 2

    # 删除源列
    df_sig_kidney.drop(['tongue', 'pulse', 'pulse0'], inplace = True, axis=1)
    df_sig_kidney.rename(columns={'pulse2':'pulse'}, inplace = True)

    # 转化成one-hot
    df_sig_kidney['sex_1'],df_sig_kidney['sex_2'],df_sig_kidney['pulse_0'],df_sig_kidney['pulse_1'],df_sig_kidney['pulse_2'],df_sig_kidney['pulse_3'],df_sig_kidney['tongue_proper_color_0'],df_sig_kidney['tongue_proper_color_1'],df_sig_kidney['tongue_proper_color_2'],df_sig_kidney['tongue_proper_color_3'],df_sig_kidney['tongue_moss_nature_0'],df_sig_kidney['tongue_moss_nature_1'],df_sig_kidney['tongue_moss_nature_2']=[0,0,0,0,0,0,0,0,0,0,0,0,0]
    # 性别
    if df_sig_kidney.sex[0] == '1':
        df_sig_kidney['sex_1'] = 1
    elif df_sig_kidney.sex[0] == '2':
        df_sig_kidney['sex_2'] = 1
    # 脉象
    if df_sig_kidney.pulse[0] == 0:
        df_sig_kidney['pulse_0'] = 1
    elif df_sig_kidney.pulse[0] == 1:
        df_sig_kidney['pulse_1'] = 1
    elif df_sig_kidney.pulse[0] == 2:
        df_sig_kidney['pulse_2'] = 1
    elif df_sig_kidney.pulse[0] == 3:
        df_sig_kidney['pulse_3'] = 1
    # 舌色
    if df_sig_kidney.tongue_proper_color[0] == 0:
        df_sig_kidney['tongue_proper_color_0'] = 1
    elif df_sig_kidney.tongue_proper_color[0] == 1:
        df_sig_kidney['tongue_proper_color_1'] = 1
    elif df_sig_kidney.tongue_proper_color[0] == 2:
        df_sig_kidney['tongue_proper_color_2'] = 1
    elif df_sig_kidney.tongue_proper_color[0] == 3:
        df_sig_kidney['tongue_proper_color_3'] = 1

    # 苔质
    if df_sig_kidney.tongue_moss_nature[0] == 0:
        df_sig_kidney['tongue_moss_nature_0'] = 1
    elif df_sig_kidney.tongue_moss_nature[0] == 1:
        df_sig_kidney['tongue_moss_nature_1'] = 1
    elif df_sig_kidney.tongue_moss_nature[0] == 2:
        df_sig_kidney['tongue_moss_nature_2'] = 1

    df_sig_kidney.drop(['sex', 'pulse', 'tongue_proper_color','tongue_moss_nature'], inplace=True, axis=1)

    # 测试的单数据格式如下array([[1,2,3,4]])
    classification = model.predict(df_sig_kidney.values)
    #print(classification)
    return classification

def multi_predict(num,cursor):
    kindneyType = ['肾阳虚', '肾阴虚']
    # 读取数据，随机选择num个样本进行验证
    #改成读数据库，随机挑选的样本，应该是判断有脉象表格的,过滤空cell数据
    sql = "select id,sex,age,serum_creatinine,eGFR,symptoms_type,tongue,pulse from dwd_kidney_info where trim(id) != '' and trim(sex) != '' and trim(age) != '' and trim(serum_creatinine) != '' and trim(eGFR) != '' and trim(symptoms_type) != '' and trim(tongue) != '' and trim(pulse) != ''"
    cursor.execute(sql)  # 获得所有符合条件的数据
    dataSet = cursor.fetchall()
    kindeySet = np.array(dataSet)
    indexs = random.sample(range(0, kindeySet.shape[0]), num)
    idSet=[]
    predictType=[]
    labelType=[]
    correct=0
    total=num
    tempParms = {'sex': '1', 'userage': '37', 'bloodCreatinine': '124.9', 'egfr': '73.953822', 'Tou': '舌红少苔',
             'pulseType': '弦细'}
    for index in indexs:
        idSet.append(kindeySet[index, 0])
        tempParms['sex']=kindeySet[index,1]
        tempParms['userage']=kindeySet[index,2]
        tempParms['bloodCreatinine']=kindeySet[index,3]
        tempParms['egfr']=kindeySet[index,4]
        tempParms['Tou']=kindeySet[index,6]
        tempParms['pulseType']=kindeySet[index,7]
        predictIndex = sigle_predict(tempParms)[0]-1
        labelIndex=int(kindeySet[index, 5])-1
        predictType.append(kindneyType[predictIndex])
        labelType.append(kindneyType[labelIndex])
        if(predictIndex==labelIndex):
            correct+=1
    accuracy = round(correct / total,4)
    return idSet,predictType,labelType,correct,total,accuracy

# if __name__ == '__main__':
# 
#     df_kidney = process_data()
#     #train_model(df_kidney)
#     dict1 = {'sex': '1', 'userage': '37', 'bloodCreatinine': '124.9', 'egfr': '73.953822', 'Tou': '舌红少苔',
#              'pulseType': '弦细'}
# 
#     sigle_predict(dict1)
