import pandas as pd
from sqlalchemy import create_engine
import os
import time

# 连接数据库
engine = create_engine("mysql+pymysql://root:000000@58.199.160.140:3306/medical_dw?charset=utf8")

# 肾科数据
def load_kidney_info_to_mysql(path, encoding='utf-8'):
    kidney_col_names = ['id', 'sex', 'age', 'staging', 'serum_creatinine', 'eGFR', 'symptoms_type', 'tongue', 'pulse']
    pd_kidney_info = pd.read_csv(path, encoding=encoding)
    pd_kidney_info.columns = kidney_col_names
    pd_kidney_info.to_sql(name='ods_kidney_info', con=engine, if_exists='append', index=False)

    # print(pd_kidney_info)

def load_kidney_pulse_to_mysql(path, encoding='utf-16 le'):
    readed_files = []  # 已读文件集合
    t1 = time.time()
    n = 0
    for root, dirs, files in os.walk(path):
        if len(files) != 0:
            for file in files:
                if 'csv' in file and file not in readed_files:
                    try:
                        data_path = root + '/' + file
                        pulse_data = pd.read_csv(data_path, encoding=encoding, header=None)
                        pulse_data = pulse_data.iloc[:, 0:-1]
                        # print(pulse_data)
                        if ' ' in file:
                            file = file.replace(' ', '')
                        tb_name = 'ods_kidney_pulse_' + file[0:-4].lower()  # 表名不能大写
                        print(n, data_path, tb_name)
                        # print(pulse_data)
                        pulse_data.to_sql(name=tb_name, con=engine, if_exists='replace', index=False)

                        readed_files.append(file)
                        n += 1
                    except:
                        print(file, '读取或导入mysql失败！')
    print('上传完毕，文件数：', len(readed_files), ' 耗时：', time.time()-t1, 's!')


# 肝科数据
def load_liver_info_to_mysql(path, encoding='utf-8'):
    liver_col_names = ['id', 'sex', 'age', 'ALT', 'symptoms_type', 'tongue', 'pulse']
    pd_liver_info = pd.read_csv(path, encoding=encoding)
    pd_liver_info.columns = liver_col_names
    pd_liver_info.to_sql(name='ods_liver_info', con=engine, if_exists='append', index=False)

    # print(pd_liver_info)

def load_liver_pulse_to_mysql(path, encoding='utf-16 le'):
    readed_files = []  # 已读文件集合
    t1 = time.time()
    n = 0
    for root, dirs, files in os.walk(path):
        if len(files) != 0:
            for file in files:
                if 'csv' in file and file not in readed_files:
                    try:
                        data_path = root + '/' + file
                        pulse_data = pd.read_csv(data_path, encoding=encoding, header=None)
                        pulse_data = pulse_data.iloc[:, 0:-1]
                        # print(pulse_data)
                        if ' ' in file:
                            file = file.replace(' ', '')
                        tb_name = 'ods_liver_pulse_' + file[0:-4].lower()  # 表名不能大写
                        print(n, data_path, tb_name)
                        pulse_data.to_sql(name=tb_name, con=engine, if_exists='replace', index=False)

                        readed_files.append(file)
                        n += 1
                    except:
                        print(file, '读取或导入mysql失败！')
    print('上传完毕，文件数：', len(readed_files), ' 耗时：', time.time() - t1, 's!')

def check_contain_chinese(check_str):
    # 判断字符串中是否含中文
    for ch in check_str:
        if ord(ch) > 255:
            return True
    return False


# 肺科数据
def load_lung_info_to_mysql(path, encoding='utf-8'):
    lung_col_names = ['id', 'sex', 'age', 'wm_diagnosis', 'lung_qi_deficiency', 'spleen_qi_deficiency', 'kidney_qi_deficiency',
                      'FEV1', 'FVC', 'FEV1%', 'FEV1/FVC', 'PEF', 'tongueA', 'tongueB', 'tongueC', 'pulseA', 'pulseB', 'pulseC']
    pd_lung_info = pd.read_csv(path, encoding=encoding)
    pd_lung_info.columns = lung_col_names
    pd_lung_info.to_sql(name='ods_lung_info', con=engine, if_exists='append', index=False)

    # print(pd_lung_info)

def load_lung_pulse_to_mysql(path, encoding='utf-16 le'):
    readed_files = []  # 已读文件集合
    t1 = time.time()
    n = 0
    for root, dirs, files in os.walk(path):
        if len(files) != 0:
            for file in files:
                if 'csv' in file and file not in readed_files:
                    try:
                        data_path = root + '/' + file
                        pulse_data = pd.read_csv(data_path, encoding=encoding, header=None)
                        pulse_data = pulse_data.iloc[:, 0:-1]
                        # print(pulse_data)
                        if ' ' in file:
                            file = file.replace(' ', '')                  # 表名不能有空格
                        # tb_name = 'ods_lung_pulse_' + file[0:-4].lower()  # 表名不能大写
                        tb_name = 'ods_lung_pulse_' + file[0:5].lower()
                        print(n, data_path, tb_name)
                        pulse_data.to_sql(name=tb_name, con=engine, if_exists='replace', index=False)

                        readed_files.append(file)
                        n += 1
                    except:
                        print(file, '读取或导入mysql失败！')
    print('上传完毕，文件数：', len(readed_files), ' 耗时：', time.time() - t1, 's!')


# 批量文件重命名处理
def file_rename(path):
    for root, dirs, files in os.walk(path):
        if len(files) != 0:
            for file in files:
                if 'L' not in file:
                    newname = 'L' + file
                    print(file, newname)
                    os.rename(os.path.join(path, file), os.path.join(path, newname))

# 清空文件夹
def clear_folder(path):
    print('清空临时文件夹...')
    for i in os.listdir(path):
        path_file = os.path.join(path, i)
        if os.path.isfile(path_file):
            os.remove(path_file)
        else:
            for f in os.listdir(path_file):
                path_file2 = os.path.join(path_file, f)
                if os.path.isfile(path_file2):
                    os.remove(path_file2)




if __name__ == '__main__':
    print('载入肾病数据...')
    path_kidney_info = 'C:/Users/Lenovo/Desktop/医疗数据/kidney_info.csv'
    load_kidney_info_to_mysql(path_kidney_info)
    #
    # path_kidney_pulse = 'C:/Users/Lenovo/Desktop/医疗数据/肾病脉诊仪'
    # load_kidney_pulse_to_mysql(path_kidney_pulse)

    # print('\n载入肝病数据...')
    # path_liver_info = 'C:/Users/Lenovo/Desktop/医疗数据/liver_info.csv'
    # load_liver_info_to_mysql(path_liver_info)
    #
    # path_liver_pulse = 'C:/Users/Lenovo/Desktop/医疗数据/肝病脉诊仪'
    # load_liver_pulse_to_mysql(path_liver_pulse)
    #
    # print('\n载入肺病数据...')
    # path_lung_info = 'C:/Users/Lenovo/Desktop/医疗数据/lung_info.csv'
    # load_lung_info_to_mysql(path_lung_info)

    # path_lung_pulse = 'C:/Users/Lenovo/Desktop/医疗数据/肺病脉诊仪'
    # load_lung_pulse_to_mysql(path_lung_pulse)




    # file_rename(path_lung_pulse)
    #
    # path = '../tmp/'
    # clear_folder(path)



    # path_100 = 'C:/Users/Lenovo/Desktop/医疗数据/肝病脉诊仪/100.csv'

    # path='C:/Users/Lenovo/Desktop/医疗数据/肾病脉诊仪/k0870.csv'
    # pulse_data = pd.read_csv(path_100, encoding='utf-16 le', header=None)
    # print(pulse_data.iloc[:,0:-1])
    # print(pulse_data.columns.size)



    # # 构建测试数据库
    # print('载入肾病数据...')
    # path_kidney_info = 'C:/Users/Lenovo/Desktop/医疗数仓项目/testimportdata/kidney/info/kidney_info.csv'
    # load_kidney_info_to_mysql(path_kidney_info)
    #
    # path_kidney_pulse = 'C:/Users/Lenovo/Desktop/医疗数仓项目/testimportdata/kidney/pulse'
    # load_kidney_pulse_to_mysql(path_kidney_pulse)
    #
    # print('\n载入肝病数据...')
    # path_liver_info = 'C:/Users/Lenovo/Desktop/医疗数仓项目/testimportdata/liver/info/liver_info.csv'
    # load_liver_info_to_mysql(path_liver_info)
    #
    # path_liver_pulse = 'C:/Users/Lenovo/Desktop/医疗数仓项目/testimportdata/liver/pulse'
    # load_liver_pulse_to_mysql(path_liver_pulse)
    #
    # print('\n载入肺病数据...')
    # path_lung_info = 'C:/Users/Lenovo/Desktop/医疗数仓项目/testimportdata/lung/info/lung_info.csv'
    # load_lung_info_to_mysql(path_lung_info)
    #
    # path_lung_pulse = 'C:/Users/Lenovo/Desktop/医疗数仓项目/testimportdata/lung/pulse'
    # load_lung_pulse_to_mysql(path_lung_pulse)




