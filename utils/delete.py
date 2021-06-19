import pandas as pd
from sqlalchemy import create_engine
import os
import time
import pymysql

try:
    db = pymysql.connect(
             host='58.199.160.140',
             port=3306,
             user='root',
             passwd='000000',
             db ='medical_dw',
             charset='utf8'
             )
except:
    print('数据库连接失败！')
    exit(0)

cursor = db.cursor()

def load_csvfile_data_to_mysql(path):
    readed_files = []  # 已读文件集合
    t1 = time.time()
    n = 0
    for root, dirs, files in os.walk(path):
        if len(files) != 0:
            for file in files:
                if '(1)' not in file and 'csv' in file and file not in readed_files:
                    data_path = root + '/' + file
                    print(data_path)
                    tb_name = 'ods_pulse_sig_' + file[0:-4].lower()   # 表名不能大写
                    print(n, file, tb_name)
                    # pulse_data = pd.read_csv(data_path, encoding='utf-16 le', header=None)
                    # pulse_data = pulse_data.iloc[:, 0:57]
                    # print(pulse_data)
                    # pulse_data.to_sql(name=tb_name, con=engine, if_exists='replace', index=False)

                    sql = 'drop table if exists ' + tb_name
                    print(sql)
                    cursor.execute(sql)


                    readed_files.append(file)
                    n += 1
    print('上传完毕，文件数：', len(readed_files), ' 耗时：', time.time()-t1, 's!')



if __name__ == '__main__':
    path = 'C:/Users/Lenovo/Desktop/医疗数据/肾病科脉诊数据/肾病脉诊仪'
    load_csvfile_data_to_mysql(path)
