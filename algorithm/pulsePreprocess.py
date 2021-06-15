#用于从中医数据库中提取数据到本地以csv形式保存
#coding=utf-8
import time

import mysqlOperates as sqlop
import csv
import codecs
import re
import pandas as pd
import numpy as np

#MySQL数据库写入csv文件
def read_mysql_to_csv(filename,results):
    #results是数据查询出来的所有数据
    with codecs.open(filename=filename, mode='w', encoding='utf-8') as f:
        write = csv.writer(f, dialect='excel')
        for result in results:
            print(result)
            write.writerow(result)


#得到数据库中脉搏波数据的全部表名
def get_dblist():
    conn = sqlop.get_conn()
    cur = conn.cursor()
    cur.execute('SHOW TABLES')
    results = cur.fetchall()
    cur.close()
    conn.close()
    table_list = []
    str = "ods_pulse_sig"
    for result in results:
        #过滤条件1.过滤非数字结尾的表（temp）2，过滤数据大小大于患者表大小的数据
        if (str in result[0] and re.findall(r"\d*", result[0])[-2] != '' and int(
                re.findall(r"\d*", result[0])[-2]) < 707):
            table_list.append(result[0])
    return table_list

#1下载清洗过的病人表
def download_dwd_patient_info():
    conn = sqlop.get_conn()
    cur = conn.cursor()
    cur.execute('select * from dwd_patient_info')
    results = cur.fetchall()
    cur.close()
    conn.close()
    read_mysql_to_csv("dwd_patient_info.csv", results)

#2对脉象描述进行清洗
def pulse_label_clear():
    #读取csv由于下载的文件没有列名自定义列名
    df = pd.read_csv("dwd_patient_info.csv",names=['User_id', 'Gender', 'Age', 'SCR', 'eGFR', "Symptom_types", 'Tongue', "Pulse"])
    #对脉的标签描述进行处理
    df['Pulse0'] = df['Pulse'].str.replace("偏", "")
    df['Pulse0'] = df['Pulse0'].str.replace("右", "")
    df['Pulse0'] = df['Pulse0'].str.replace("左", "")
    df['Pulse0'] = df['Pulse0'].str.replace("脉", "")
    df['Pulse0'] = df['Pulse0'].str.replace("\r", "")
    df['Pulse0'] = df['Pulse0'].str.strip()
    df = df[~df['Pulse0'].isin([""])]
    df['Pulse1'] = df['Pulse0'].str[0]
    df = df[~df['Pulse1'].isin(["迟", '滑', '濡', '数', '虚'])]
    df['Pulse2'] = df['Pulse1'].str.replace("沉", "1")
    df['Pulse2'] = df['Pulse2'].str.replace("细", "2")
    df['Pulse2'] = df['Pulse2'].str.replace("弦", "3")
    #分成沉细-0，沉-1，细-2，弦细-3四类，主要是数据就这四类最多
    new_df = pd.DataFrame()
    #提取包含某字符的df
    df1 = df[df['Pulse0'].str.contains("沉细")]
    df1.loc[:,'Pulse2'] = 0
    #连接df
    new_df = pd.concat([df1, new_df], axis=0)
    # print(new_df)
    # 删除包含某字符的行
    df = df[~df['Pulse0'].str.contains("沉细")]
    #isin(['',''])完整的值list
    df2 = df[df['Pulse2'].isin(['1'])]
    new_df = pd.concat([df2, new_df], axis=0)
    df3 = df[df['Pulse2'].isin(['2'])]
    new_df = pd.concat([df3, new_df], axis=0)
    df4 = df[df['Pulse2'].isin(['3'])]
    new_df = pd.concat([df4, new_df], axis=0)
    #打乱顺序
    new_df = new_df.sample(frac=1).reset_index(drop=True)
    new_df.to_csv('pulse_label_clear.csv', index=False)

#3获得脉搏波表名和患者id的交集
def get_joint():
    #读取清洗后的表
    df = pd.read_csv(r"pulse_label_clear.csv")
    patient_list = df.iloc[:, [0]]
    # 数据库中病人的脉数据表名
    df_dblist = pd.DataFrame(get_dblist(), columns=["dblist"])
    df_dblist = df_dblist['dblist'].str[-5:].to_frame()
    # 患者表中的id
    patient_list.columns = ['dblist']
    patient_list = patient_list['dblist'].str[:].to_frame()
    # 交集
    ntersected_df = pd.merge(df_dblist, patient_list, how='inner')
    ntersected_df['dblist'] = ntersected_df['dblist']
    # print(ntersected_df)
    return np.array(ntersected_df['dblist']).tolist()

#4下载每个病人对应的脉搏波数据
def download_patient_pulse_csv():
    joint_lists = get_joint()
    # print(joint_lists)
    lists = get_dblist()
    # print(lists)
    conn = sqlop.get_conn()
    # print(joint_lists[0][0] in lists[0])

    for joint_list in joint_lists:
        for list in lists:
            if (joint_list in list):
                sql = "select * from " + list
                results = sqlop.select_data(conn, sql)
                filename = './data/' + list+'.csv'
                read_mysql_to_csv(filename, results)
                print("下载成功")
        time.sleep(5)
    conn.close()

#5得到重合的标签数据（有脉搏波数据的患者）
def updata_patinet_mergeid():
    joint_lists = get_joint()
    df = pd.read_csv("pulse_label_clear.csv")
    df = df[df['User_id'].isin(joint_lists)]
    df.to_csv('pulse_label_merge.csv', index=False)

if __name__ == '__main__':
    updata_patinet_mergeid()
