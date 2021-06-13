# -*- coding:utf-8 -*-
from flask import Flask, render_template, request
import pymysql
import pandas as pd
import json
from utils import tool

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
@app.route('/datastatistic', methods=["GET", "POST"])
def data_statistic():
    if request.method == "GET":
        # 从数据库获取病人信息表
        try:
            cursor.execute("SELECT sex, age, serum_creatinine, eGFR, symptoms_type FROM dwd_patient_info;")
        except:
            print('从服务器获取数据失败')
            return 0
        query_result = cursor.fetchall()
        col_names = pd.DataFrame(list(cursor.description)).iloc[:,0].tolist()
        pd_patient_info = pd.DataFrame(list(query_result), columns=col_names)

        data = tool.get_statistic_info(pd_patient_info)

        data_json = json.dumps(data)
        # return data_json
        return render_template('datastatistic.html', data_json=data_json)
    elif request.method == "POST":
        gender = request.form.get('gender')
        min_age = request.form.get('min_age')
        max_age = request.form.get('max_age')
        min_sc_value = request.form.get('min_sc_value')
        max_sc_value = request.form.get('max_sc_value')
        min_eGFR = request.form.get('min_eGFR')
        max_eGFR = request.form.get('max_eGFR')
        symptoms_type = request.form.get('symptoms_type')
        # print(gender, min_age, max_age, min_sc_value, max_sc_value, min_eGFR, max_eGFR)

        sql = "SELECT sex, age, serum_creatinine, eGFR, symptoms_type FROM dwd_patient_info WHERE id IS NOT NULL"
        t = [None, '', 'all']
        if gender in ['男', '女']:
            sql = sql + " AND sex=" + ('1' if gender=='男' else '2')
        if min_age not in t:
            sql = sql + " AND age>=" + str(min_age)
        if max_age not in t:
            sql = sql + " AND age<=" + str(max_age)
        if min_sc_value not in t:
            sql = sql + " AND serum_creatinine>=" + str(min_sc_value)
        if max_sc_value not in t:
            sql = sql + " AND serum_creatinine<=" + str(max_sc_value)
        if min_eGFR not in t:
            sql = sql + " AND eGFR>=" + str(min_eGFR)
        if min_sc_value not in t:
            sql = sql + " AND eGFR>=" + str(max_eGFR)
        if symptoms_type in ['肾阳虚', '肾阴虚']:
            sql = sql + " AND symptoms_type=" + ('1' if symptoms_type=='肾阳虚' else '2')
        # print(sql)

        # 从数据库获取病人信息表
        try:
            cursor.execute(sql)
        except:
            print('从服务器获取数据失败')
            return 0
        query_result = cursor.fetchall()
        col_names = pd.DataFrame(list(cursor.description)).iloc[:, 0].tolist()
        pd_patient_info = pd.DataFrame(list(query_result), columns=col_names)
        print(pd_patient_info)

        data = tool.get_statistic_info(pd_patient_info)

        data_json = json.dumps(data)
        # return data_json
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