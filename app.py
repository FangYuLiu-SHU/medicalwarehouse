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



# 病人信息展示页面
@app.route('/patient_info_show')
def patient_info_show():
    return render_template('patient_info.html',page_data=json.dumps([]))


@app.route('/patient_info_by_condition',methods=['POST'])
def patient_info_by_condition():
    page = request.form.get('page')  # 页数
    limit = request.form.get('limit')  # 每页显示的数量
    if page is None:
        page=1
    if limit is None:
        limit=1
    id = request.form.get('id')  # 编号
    sex = request.form.get('sex')  # 性别
    age = json.loads(request.form.get('age'))  # 年龄
    serum_creatinine = json.loads(request.form.get('serum_creatinine'))  # 血肌酐
    eGFR = json.loads(request.form.get('eGFR'))
    symptoms = request.form.get('symptoms')  # 症型(1=肾阳虚，2=肾阴虚)
    sql = "select * from dwd_patient_info where 1=1 "
    if id!="":
        sql+="and id='" + str(id) + "'"
    if sex!="":
        sql += "and sex='" + str(sex) + "'"
    if age[0]!="" :
        sql += "and age>'" + str(age[0]) + "'"
    if age[1]!="" :
        sql += "and age<'" +  str(age[1]) + "'"
    if serum_creatinine[0]!="":
        sql += "and serum_creatinine>'" + str(serum_creatinine[0]) + "'"
    if serum_creatinine[1]!="":
        sql += "and serum_creatinine<'" +  str(serum_creatinine[1]) + "'"
    if eGFR[0]!="":
        sql += "and eGFR>'" + str(eGFR[0]) + "'"
    if eGFR[1]!="":
        sql += "and eGFR<'" +  str(eGFR[1]) + "'"
    if symptoms!="":
        sql += "and symptoms_type='" + str(symptoms) + "'"
    offset = (int(page) - 1) * int(limit)  # 起始行
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()
    sql+="limit "+str(offset)+','+str(limit)
    # sql_total_count = "select count(*) from dwd_patient_info"  # 总的记录数
    # cursor.execute(sql_total_count)  # 执行sql语句
    # patient_total_count = cursor.fetchall()  # 取数据
    cursor.execute(sql)
    data = cursor.fetchall()
    json_data = {}
    result_data = []
    for result in data:
        result_data.append({
            'id': str(result[0]),
            'sex': str(result[1]),
            'age': str(result[2]),
            'serum_creatinine': str(result[3]),
            'eGFR': str(result[4]),
            'symptoms_type': str(result[5]),
            'tongue': str(result[6]),
            'pulse': str(result[7]).strip(),
        })
    json_data["code"] = str(0)
    json_data['total'] = len(totalQueryData)
    json_data['data'] = result_data
    json_data = json.dumps(json_data, ensure_ascii=False)
    return json_data

if __name__ == '__main__':
    app.run(debug=True)