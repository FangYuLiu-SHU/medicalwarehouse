#使用svm对肾表的症状进行二分类
# 导入第三方模块
from imblearn.over_sampling import SMOTE
from sklearn import svm
import joblib
from sklearn import model_selection
from sklearn import metrics
import pandas as pd
import re
import random
import numpy as np

def liver_tongue_pulse_code(df_liver):
    # 对脉的标签描述进行清洗
    df_liver['pulse0'] = df_liver['pulse'].str.replace("偏", "")
    df_liver['pulse0'] = df_liver['pulse0'].str.replace("右", "")
    df_liver['pulse0'] = df_liver['pulse0'].str.replace("左", "")
    df_liver['pulse0'] = df_liver['pulse0'].str.replace("脉", "")
    df_liver['pulse0'] = df_liver['pulse0'].str.replace("\r", "")
    df_liver['pulse0'] = df_liver['pulse0'].str.strip()
    df_liver = df_liver[~df_liver['pulse0'].isin([""])]
    # 对脉的标签描述进行编码
    # 其他-0 沉-1 细-2 弦-3
    # 其它默认0
    df_liver['pulse2'] = 0
    pat0 = '沉.*'
    df_liver.loc[~df_liver['pulse0'].apply(lambda x: re.match(pat0, x)).isna(), 'pulse2'] = 1
    pat1 = '细.*'
    df_liver.loc[~df_liver['pulse0'].apply(lambda x: re.match(pat1, x)).isna(), 'pulse2'] = 2
    pat2 = '弦.*'
    df_liver.loc[~df_liver['pulse0'].apply(lambda x: re.match(pat2, x)).isna(), 'pulse2'] = 3

    # 对舌的标签描述进行编码
    df_liver['tongue_proper_color'] = 0  # 舌质颜色 淡红（正常）-0 淡白-1 红-2 暗/紫-3
    df_liver['tongue_proper_shape_pang'] = 0  # 舌质形态 正常-0 胖-1    裂纹(太少不用)  嫩 胖 齿印
    df_liver['tongue_proper_shape_neng'] = 0  # 舌质形态 正常-0  嫩-1
    df_liver['tongue_proper_shape_chiyin'] = 0  # 舌质形态 正常-0  齿印-1
    df_liver['tongue_moss_color'] = 0  # 苔色白（正常）-0、黄-1
    df_liver['tongue_moss_nature'] = 0  # 苔质 薄（正常）-0  少-1  腻-2 厚（4个样本不用了）薄少和润滑（不用）燥糙和腐腻
    # 舌色编码
    patt0 = r'.*淡(?!红).*'
    df_liver.loc[~df_liver['tongue'].apply(lambda x: re.match(patt0, x)).isna(), 'tongue_proper_color'] = 1
    patt1 = r'.*[^淡]红.*'
    df_liver.loc[~df_liver['tongue'].apply(lambda x: re.match(patt1, x)).isna(), 'tongue_proper_color'] = 2
    df_liver.loc[df_liver['tongue'].str.contains('暗'), 'tongue_proper_color'] = 3
    df_liver.loc[df_liver['tongue'].str.contains('紫'), 'tongue_proper_color'] = 3
    # 舌形编码
    df_liver.loc[df_liver['tongue'].str.contains('胖'), 'tongue_proper_shape_pang'] = 1
    df_liver.loc[df_liver['tongue'].str.contains('嫩'), 'tongue_proper_shape_neng'] = 1
    df_liver.loc[df_liver['tongue'].str.contains('齿'), 'tongue_proper_shape_chiyin'] = 1
    # 苔色编码
    df_liver.loc[df_liver['tongue'].str.contains('黄'), 'tongue_moss_color'] = 1
    # 苔质编码
    df_liver.loc[df_liver['tongue'].str.contains('少'), 'tongue_moss_nature'] = 1
    df_liver.loc[df_liver['tongue'].str.contains('腻'), 'tongue_moss_nature'] = 2
    return df_liver

def process_data():
    # 读取数据
    df_liver = pd.read_csv('./files/dwd_liver_info.csv')
    # 获得编码
    df_liver = liver_tongue_pulse_code(df_liver)
    # 拼接
    # df_liver = pd.concat([df_liver, df], axis=1)

    symptoms_type = df_liver['symptoms_type']
    # 删除不需要的列
    df_liver.drop(['id', 'tongue', 'pulse', 'pulse0', 'symptoms_type'], inplace=True, axis=1)
    # 把标签Y移到第一列方便操作
    df_liver.insert(0, 'symptoms_type', symptoms_type)
    # 修改名称
    df_liver.rename(columns={'pulse2': 'pulse'}, inplace=True)

    # 将数值型的sex，pulse，tongue_proper_color转换为类别型，否则无法对其哑变量处理
    df_liver.sex = df_liver.sex.astype('category')
    df_liver.pulse = df_liver.pulse.astype('category')
    df_liver.tongue_proper_color = df_liver.tongue_proper_color.astype('category')
    df_liver.tongue_moss_nature = df_liver.tongue_moss_nature.astype('category')

    df_liver.tongue_proper_shape_pang = df_liver.tongue_proper_shape_pang.astype('category')
    df_liver.tongue_proper_shape_neng = df_liver.tongue_proper_shape_neng.astype('category')
    df_liver.tongue_proper_shape_chiyin = df_liver.tongue_proper_shape_chiyin.astype('category')
    df_liver.tongue_moss_color = df_liver.tongue_moss_color.astype('category')

    # 哑变量处理
    dummy = pd.get_dummies(df_liver[['sex', 'pulse', 'tongue_proper_color','tongue_moss_nature']])
    df_liver.drop(['sex', 'pulse','tongue_proper_color' ,'tongue_moss_nature'], inplace=True, axis=1)

    df_liver = pd.concat([df_liver, dummy], axis=1)

    # 由于数据集分布不均衡使用SMOTE进行过采样 原Counter({2: 173, 1: 15})
    X = df_liver.iloc[:, 1:]
    Y = df_liver.symptoms_type
    # 定义SMOTE模型，random_state相当于随机数种子的作用
    smo = SMOTE(random_state=0)
    X_smo, Y_smo = smo.fit_resample(X, Y)
    df_liver = pd.concat([Y_smo, X_smo], axis=1)
    # 删除空值 现在 Counter({2: 173, 1: 173})
    df_liver.dropna(inplace=True)
    return df_liver

def train_model(df_liver):
    # 将数据拆分为训练集和测试集
    X_train, X_test, y_train, y_test = model_selection.train_test_split(df_liver.iloc[:, 1:], df_liver.symptoms_type,
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
    joblib.dump(linear_svc, './files/SVM_liver_predict.pkl')


def sigle_predict(dict):
    # 加载模型
    model = joblib.load('./files/SVM_liver_predict.pkl')

    #dict1 = {'sex': '2', 'agess': '59', 'ALTs': '110.5','Tou':'舌淡齿痕苔腻', 'pulseType': '细'}
    df_sig_liver = pd.DataFrame(dict, index=[0])
    # 重命名
    df_sig_liver.columns = ['sex', 'age', 'ALT', 'tongue', 'pulse']
    # 脉清洗
    df_sig_liver['pulse0'] = df_sig_liver['pulse'].str.replace("偏", "").str.replace("右", "").str.replace("左", "").str.replace("脉", "").str.replace("\r", "").str.strip()
    # 脉编码
    df_sig_liver['pulse2'] = 0
    pat0 = '沉.*'
    df_sig_liver.loc[~df_sig_liver['pulse0'].apply(lambda x: re.match(pat0, x)).isna(), 'pulse2'] = 1
    pat1 = '细.*'
    df_sig_liver.loc[~df_sig_liver['pulse0'].apply(lambda x: re.match(pat1, x)).isna(), 'pulse2'] = 2
    pat2 = '弦.*'
    df_sig_liver.loc[~df_sig_liver['pulse0'].apply(lambda x: re.match(pat2, x)).isna(), 'pulse2'] = 3

    # 对舌的标签描述进行编码
    df_sig_liver['tongue_proper_color'] = 0  # 舌质颜色 淡红（正常）-0 淡白-1 红-2 暗/紫-3
    df_sig_liver['tongue_proper_shape_pang'] = 0  # 舌质形态 正常-0 胖-1    裂纹(太少不用)  嫩 胖 齿印
    df_sig_liver['tongue_proper_shape_neng'] = 0  # 舌质形态 正常-0  嫩-1
    df_sig_liver['tongue_proper_shape_chiyin'] = 0  # 舌质形态 正常-0  齿印-1
    df_sig_liver['tongue_moss_color'] = 0  # 苔色白（正常）-0、黄-1
    df_sig_liver['tongue_moss_nature'] = 0  # 苔质 薄（正常）-0  少-1  腻-2 厚（4个样本不用了）薄少和润滑（不用）燥糙和腐腻
    # 舌色编码
    patt0 = r'.*淡(?!红).*'
    df_sig_liver.loc[~df_sig_liver['tongue'].apply(lambda x: re.match(patt0, x)).isna(), 'tongue_proper_color'] = 1
    patt1 = r'.*[^淡]红.*'
    df_sig_liver.loc[~df_sig_liver['tongue'].apply(lambda x: re.match(patt1, x)).isna(), 'tongue_proper_color'] = 2
    df_sig_liver.loc[df_sig_liver['tongue'].str.contains('暗'), 'tongue_proper_color'] = 3
    df_sig_liver.loc[df_sig_liver['tongue'].str.contains('紫'), 'tongue_proper_color'] = 3
    # 舌形编码
    df_sig_liver.loc[df_sig_liver['tongue'].str.contains('胖'), 'tongue_proper_shape_pang'] = 1
    df_sig_liver.loc[df_sig_liver['tongue'].str.contains('嫩'), 'tongue_proper_shape_neng'] = 1
    df_sig_liver.loc[df_sig_liver['tongue'].str.contains('齿'), 'tongue_proper_shape_chiyin'] = 1
    # 苔色编码
    df_sig_liver.loc[df_sig_liver['tongue'].str.contains('黄'), 'tongue_moss_color'] = 1
    # 苔质编码
    df_sig_liver.loc[df_sig_liver['tongue'].str.contains('少'), 'tongue_moss_nature'] = 1
    df_sig_liver.loc[df_sig_liver['tongue'].str.contains('腻'), 'tongue_moss_nature'] = 2

    # 删除源列
    df_sig_liver.drop(['tongue', 'pulse', 'pulse0'], inplace = True, axis=1)
    df_sig_liver.rename(columns={'pulse2':'pulse'}, inplace = True)

    # 转化成one-hot
    df_sig_liver['sex_1'],df_sig_liver['sex_2'],df_sig_liver['pulse_0'],df_sig_liver['pulse_1'],df_sig_liver['pulse_2'],df_sig_liver['pulse_3'],df_sig_liver['tongue_proper_color_0'],df_sig_liver['tongue_proper_color_1'],df_sig_liver['tongue_proper_color_2'],df_sig_liver['tongue_proper_color_3'],df_sig_liver['tongue_moss_nature_0'],df_sig_liver['tongue_moss_nature_1'],df_sig_liver['tongue_moss_nature_2']=[0,0,0,0,0,0,0,0,0,0,0,0,0]
    # 性别
    if df_sig_liver.sex[0] == '1':
        df_sig_liver['sex_1'] = 1
    elif df_sig_liver.sex[0] == '2':
        df_sig_liver['sex_2'] = 1
    # 脉象
    if df_sig_liver.pulse[0] == 0:
        df_sig_liver['pulse_0'] = 1
    elif df_sig_liver.pulse[0] == 1:
        df_sig_liver['pulse_1'] = 1
    elif df_sig_liver.pulse[0] == 2:
        df_sig_liver['pulse_2'] = 1
    elif df_sig_liver.pulse[0] == 3:
        df_sig_liver['pulse_3'] = 1
    # 舌色
    if df_sig_liver.tongue_proper_color[0] == 0:
        df_sig_liver['tongue_proper_color_0'] = 1
    elif df_sig_liver.tongue_proper_color[0] == 1:
        df_sig_liver['tongue_proper_color_1'] = 1
    elif df_sig_liver.tongue_proper_color[0] == 2:
        df_sig_liver['tongue_proper_color_2'] = 1
    elif df_sig_liver.tongue_proper_color[0] == 3:
        df_sig_liver['tongue_proper_color_3'] = 1

    # 苔质
    if df_sig_liver.tongue_moss_nature[0] == 0:
        df_sig_liver['tongue_moss_nature_0'] = 1
    elif df_sig_liver.tongue_moss_nature[0] == 1:
        df_sig_liver['tongue_moss_nature_1'] = 1
    elif df_sig_liver.tongue_moss_nature[0] == 2:
        df_sig_liver['tongue_moss_nature_2'] = 1

    df_sig_liver.drop(['sex', 'pulse', 'tongue_proper_color','tongue_moss_nature'], inplace=True, axis=1)

    # 测试的单数据格式如下array([[1,2,3,4]])
    classification = model.predict(df_sig_liver.values)
    #print(classification)
    return classification

def multi_predict(num,cursor):
    Type = ['肝胆湿热症', '肝郁脾虚症']
    # 读取数据，随机选择num个样本进行验证
    # 改成读数据库，随机挑选的样本，应该是判断有脉象表格的,过滤空cell数据
    sql = "select * from dwd_liver_info where trim(id) != '' and trim(sex) != '' and trim(age) != '' and trim(ALT) != '' and trim(symptoms_type) != '' and trim(tongue) != '' and trim(pulse) != ''"
    cursor.execute(sql)  # 获得所有符合条件的数据
    dataSet = cursor.fetchall()
    set = np.array(dataSet)
    indexs = random.sample(range(0, set.shape[0]), num)
    idSet=[]
    predictType=[]
    labelType=[]
    correct=0
    total=num
    tempParms = {'sex': '2', 'userage': '65', 'ALTD': '30', 'Tou': '舌苔黄腻', 'pulseType': '弦数'}
    for index in indexs:
        idSet.append(set[index, 0])
        tempParms['sex']=set[index,1]
        tempParms['userage']=set[index,2]
        tempParms['ALTD']=set[index,3]
        tempParms['Tou']=set[index,5]
        tempParms['pulseType']=set[index,6]
        predictIndex = sigle_predict(tempParms)[0]-1
        labelIndex=int(set[index, 4])-1
        predictType.append(Type[predictIndex])
        labelType.append(Type[labelIndex])
        if(predictIndex==labelIndex):
            correct+=1
    accuracy = round(correct / total,4)
    return idSet,predictType,labelType,correct,total,accuracy

# if __name__ == '__main__':
# 
#     df_liver = process_data()
#     train_model(df_liver)
#     dict1 = {'sex': '2', 'userage': '65', 'ALTD': '30', 'Tou': '舌苔黄腻', 'pulseType': '弦数'}
#     sigle_predict(dict1)
