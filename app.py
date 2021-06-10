# -*- coding:utf-8 -*-
from flask import Flask, render_template, request
import pymysql
import pandas as pd
import json


# 连接数据库
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

# 使用cursor()方法创建一个游标对象cursor，用于执行SQL语句
cursor = db.cursor()

# # 关闭数据库连接
# db.close()


app = Flask(__name__)
app.secret_key = '000000'



@app.route('/')
def hello_world():
    return render_template('index.html')

# 数据统计
@app.route('/datastatistic')
def data_statistic():
    # 从数据库获取病人信息表
    cursor.execute("SELECT * FROM dwd_patient_info;")
    query_result = cursor.fetchall()
    col_names = pd.DataFrame(list(cursor.description)).iloc[:,0].tolist()
    pd_patient_info = pd.DataFrame(list(query_result), columns=col_names)

    num_patient = len(pd_patient_info)  # 病人个数
    num_male = len(pd_patient_info[pd_patient_info['sex']=='1'])    # 男性个数
    num_female = len(pd_patient_info[pd_patient_info['sex']=='2'])  # 女性个数

    num_pos = len(pd_patient_info[pd_patient_info['symptoms_type'] == '1'])  # 肾阳虚个数
    num_neg = len(pd_patient_info[pd_patient_info['symptoms_type'] == '2'])  # 肾阴虚个数

    # 年龄段统计
    age_distribute = {}
    for i in range(10):
        min_age = 10*i
        max_age = 10*(i+1)
        tmp = pd_patient_info[pd_patient_info['age'] >= min_age]
        num = len(tmp[tmp['age'] < max_age])
        age_range = str(min_age) + '-' + str(max_age)
        age_distribute.update({age_range:num})

    # 所有要传给前端的数据
    data = {
        'num_patient': num_patient,     # 病人个数
        'num_male': num_male,           # 男性个数
        'num_female': num_female,       # 女性个数
        'num_pos': num_pos,             # 肾阳虚病人个数
        'num_neg': num_neg,             # 肾阴虚病人个数
        'age_distribute': age_distribute# 年龄段分布
    }

    data_json = json.dumps(data)
    return render_template('datastatistic.html', data_json=data_json)


# 病人信息展示
@app.route('/patient_info')
def patient_info():
    page = request.args.get('page')  # 页数
    limit = request.args.get('limit')  # 每页显示的数量
    err="false" #返回错误信息
    if page is None and limit is None:
        err="true"
        return render_template('patient_info.html',page_data=json.dumps([]),err=err )
    else:
        sql_total_count = "select count(*) from dwd_patient_info"  # 总的记录数
        cursor.execute(sql_total_count)  # 执行sql语句
        patient_total_count = cursor.fetchall()  # 取数据

        err = inputJudge(page, limit, int(patient_total_count[0][0]), err)
        if err != "false":
            print(err)
            return render_template('patient_info.html', page_data=json.dumps([]), err=err)

    offset = (int(page) - 1) * int(limit)  # 起始行
    sql = "select * from dwd_patient_info limit " + str(offset) + ',' + str(limit)  # 一页数据
    cursor.execute(sql)  # 执行sql语句
    data = cursor.fetchall()  # 获取数据
    json_data = {}
    one_page_data = []
    for result in data:
        each_person = []
        each_person.append({
            'id': str(result[0]),
            'sex': str(result[1]),
            'age': str(result[2]),
            'serum_creatinine': str(result[3]),
            'eGFR': str(result[4]),
            'symptoms_type': str(result[5]),
            'tongue': str(result[6]),
            'pulse': str(result[7]).strip(),
        })
        one_page_data.append(each_person)
        json_data["code"] = str(0)
        json_data['total'] = patient_total_count[0][0]
        json_data['data'] = one_page_data
    json_data=json.dumps(json_data,ensure_ascii=False)
    print(json_data)
    return render_template('patient_info.html', page_data=json_data, err=err)
    

if __name__ == '__main__':
    app.run(debug=True)