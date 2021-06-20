#用于从中医数据库中提取脉搏相关数据和标签进行预处理和编码，为深度学习做准备
#coding=utf-8
import time
import mysqlOperates as sqlop
import csv
import codecs
import re
import pandas as pd
import numpy as np

def get_df_info():
    # 从数据库读取三表数据
    # df_kidney_info = pd.read_sql('select * from dwd_kidney_info', sqlop.get_conn())
    # df_liver_info = pd.read_sql('select * from dwd_liver_info', sqlop.get_conn())
    # df_lung_info = pd.read_sql('select * from dwd_lung_info', sqlop.get_conn())

    #读取原数据
    df_kidney_info = pd.read_excel(r'肾.xlsx')
    df_kidney_info.columns = ['id', 'sex', 'age', 'stage', 'serum_creatinine', 'eGFR', 'symptoms_type', 'tongue',
                              'pulse']
    df_kidney_info.drop(['stage'], axis=1, inplace=True)
    df_lung_info = pd.read_excel(r'肺.xls')
    df_lung_info.columns = ['id', 'name', 'sex', 'age', 'wm_diagnosis', 'Lung_qi_deficiency', 'spleen_qi_deficiency',
                            'kidney_qi_deficiency', 'FEV1', 'FVC', 'FEV1%', 'FEV1/FVC', 'PEF', 'tongue', 'tongueB',
                            'tongueC', 'pulse', 'pulseB', 'pulseC']
    df_liver_info = pd.read_excel(r'肝.xlsx')
    df_liver_info.columns = ['id', 'sex', 'age', 'ALT', 'symptoms_type', 'tongue', 'pulse']
    # 保存到本地
    # df_kidney_info.to_csv('dwd_kidney_info.csv',index=False)
    # df_liver_info.to_csv('dwd_liver_info.csv', index=False)
    # df_lung_info.to_csv('dwd_lung_info.csv', index=False)

    # 提取id和pulse列并且合并
    df_kidney_info = df_kidney_info.loc[:, ['id', 'pulse']]
    df_lung_info = df_lung_info.loc[:, ['id', 'pulse']]
    df_liver_info = df_liver_info.loc[:, ['id', 'pulse']]
    df_info = df_kidney_info.append(df_lung_info).append(df_liver_info)
    return df_info

def clear_and_code(df_info):
    # 总共1222例:
    #     沉309（沉细-260；沉-32；其他<10）
    #     细468（细-369，细数-41，细弦-21，其他<10）
    #     弦191（弦-78，弦细-84，其他<10）
    #     滑85
    #     濡76
    #     弱30
    #     浮19
    #     缓12
    #     数10
    #     虚7
    #     涩3
    #     微3
    #     正常2
    df_info['pulse0'] = df_info['pulse'].copy().str.replace("偏", "")
    df_info['pulse0'] = df_info['pulse0'].str.replace("右", "")
    df_info['pulse0'] = df_info['pulse0'].str.replace("左", "")
    df_info['pulse0'] = df_info['pulse0'].str.replace("脉", "")
    df_info['pulse0'] = df_info['pulse0'].str.replace("尺", "")
    df_info['pulse0'] = df_info['pulse0'].str.strip()
    df_info = df_info[~df_info['pulse0'].isin([""])]
    df_info.dropna(inplace=True)
    df_info['pulse1'] = df_info['pulse0'].str[0]

    # 分类方案：方案一：沉细-0 细-1 弦-2 弦细-3 滑-4 濡-5  方案二：其他-0 沉-1 细-2 弦-3
    # 方案一
    df_info = df_info[~df_info['pulse1'].isin(['迟', '浮', '缓','结','弱','涩','数','虚','微','正'])]

    #沉细默认0
    df_info['pulse2'] = 0

    #删除沉脉中除沉细的数据
    pat0 = '沉(?!细).*'
    df_info = df_info[df_info['pulse0'].apply(lambda x: re.match(pat0, x)).isna()]

    pat1 = '细.*'
    df_info.loc[~df_info['pulse0'].apply(lambda x: re.match(pat1, x)).isna(), 'pulse2'] = 1

    pat2 = '弦(?!细).*'
    df_info.loc[~df_info['pulse0'].apply(lambda x: re.match(pat2, x)).isna(), 'pulse2'] = 2
    df_info.loc[df_info['pulse0'].str.contains('弦细'),'pulse2'] = 3

    pat3 = '滑.*'
    df_info.loc[~df_info['pulse0'].apply(lambda x: re.match(pat3, x)).isna(), 'pulse2'] = 4

    pat4 = '濡.*'
    df_info.loc[~df_info['pulse0'].apply(lambda x: re.match(pat4, x)).isna(), 'pulse2'] = 5

    # #方案二 沉、细、弦、其它，四分类
    # #其它默认0
    # df_info['pulse2'] = 0

    # pat0 = '沉.*'
    # df_info.loc[~df_info['pulse0'].apply(lambda x: re.match(pat0, x)).isna(), 'pulse2'] = 1

    # pat1 = '细.*'
    # df_info.loc[~df_info['pulse0'].apply(lambda x: re.match(pat1, x)).isna(), 'pulse2'] = 2

    # pat2 = '弦.*'
    # df_info.loc[~df_info['pulse0'].apply(lambda x: re.match(pat2, x)).isna(), 'pulse2'] = 3
    df_info_clear_code = df_info
    df_info_clear_code['id'] = df_info_clear_code['id'].str.lower()
    df_info_clear_code.drop_duplicates('id','first',inplace=True)
    df_info_clear_code.to_csv('df_info_clear_code.csv')
    return df_info_clear_code

def get_df_pulse_data_name_lists():
    # 得到ods表名称--数据库中病人的脉数据表名
    conn = sqlop.get_conn()
    cur = conn.cursor()
    cur.execute('SHOW TABLES')
    results = cur.fetchall()
    cur.close()
    conn.close()
    table_list = []
    str = "ods"
    for result in results:
        if (str in result[0]):
            table_list.append(result[0])
    df_pulse_data_name_lists = pd.DataFrame(table_list, columns=['id'])
    return df_pulse_data_name_lists

def get_df_info_merge(df_info_clear_code):
    df_pulse_data_name_lists = get_df_pulse_data_name_lists()
    #获取ods_kidney_pulse_k0212中的k0212作为匹配对象
    df_pulse_data_name_list_temp = df_pulse_data_name_lists['id'].str.split('_', expand=True)
    df_pulse_data_name_number_list = df_pulse_data_name_list_temp.iloc[:, -1].to_frame()
    df_pulse_data_name_number_list.columns = ['id']
    # 获得脉搏波表名和患者id的交集
    df_info_merge = pd.merge(df_info_clear_code, df_pulse_data_name_number_list, how='inner')
    # print(df_info_merge)
    df_info_merge.to_csv('df_info_merge.csv',index=False)
    return df_info_merge

def download(df_info_merge):
    # 下载
    df_pulse_data_name_lists = get_df_pulse_data_name_lists()
    download_number = 0
    id_lists = df_info_merge['id'].tolist()
    for id in id_lists:
        print('id:'+id)
        download_number += 1
        for pulse_data_name in df_pulse_data_name_lists['id'].tolist():
            print('pulse_data_name:'+pulse_data_name)
            if id in pulse_data_name:
                sql = "select * from " + pulse_data_name
                df = pd.read_sql(sql,sqlop.get_conn())
                df.to_csv('data/'+pulse_data_name+'.csv',index=False)
                print('第{}个pulse数据下载成功！'.format(download_number))
                break
        time.sleep(3)
if __name__ == '__main__':
    # 步骤1 读取肝肺肾三表数据提取患者编号和脉象描述标签合并
    # 步骤2 清洗数据,脉象描述进行编码
    # 步骤3 和数据库中的ods层数据对比下载对齐数据，同时更新对齐后的表格

    df_info = get_df_info()
    df_info_clear_code = clear_and_code(df_info)
    df_info_merge = get_df_info_merge(df_info_clear_code)
    download(df_info_merge)
    # df_info.to_csv('df_info.csv')
