# -*- coding:utf-8 -*-
from flask import Flask, render_template, request
import pymysql
import pandas as pd
import json
from utils import tool
import os
from algorithm import predict

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
        return data_json
        # return render_template('datastatistic.html', data_json=data_json)


@app.route('/statistic_detail')
def statistic_detail():
    return render_template('statistic_detail.html')

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
        sql += "and age>='" + str(age[0]) + "'"
    if age[1]!="" :
        sql += "and age<='" +  str(age[1]) + "'"
    if serum_creatinine[0]!="":
        sql += "and serum_creatinine>='" + str(serum_creatinine[0]) + "'"
    if serum_creatinine[1]!="":
        sql += "and serum_creatinine<='" +  str(serum_creatinine[1]) + "'"
    if eGFR[0]!="":
        sql += "and eGFR>='" + str(eGFR[0]) + "'"
    if eGFR[1]!="":
        sql += "and eGFR<='" +  str(eGFR[1]) + "'"
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

@app.route('/disease_prediction', methods=["GET", "POST"])
def disease_prediction():
    if request.method == "GET":
        formData={'sex': '男', 'userage': '', 'stage': '', 'bloodCreatinine': '', 'egfr': '', 'fileName': '', 'pulseType': ''}
        newData = json.dumps(formData)  # json.dumps封装
        return render_template('diseasePrediction.html', newData=newData)
    if request.method == "POST":
        #获取前端请求的表单数据
        formData = request.form.to_dict()
        # 获取pulseFile文件对象
        pulseFile = request.files.get('pulseFile')
        # 保存到服务器
        # save方法传完整的路径和文件名
        # pulseFile.save(os.path.join(UPLOAD_PATH,pulseFile.filename))
        # 上行可以进行优化,下行是对pulseFile文件名进行包装，保证文件名更安全。
        filename = "pulseFile.csv"
        pulseFile.save(os.path.join("./files/", filename))
        #print(pulseFile)

        filename_in = './files/pulseFile.csv'
        #filename_out = './files/pulseFileUTF.csv'

        # 输入文件的编码类型
        #encode_in = 'utf-16 le'

        # 输出文件的编码类型
        # encode_out = 'utf-8'
        #
        # with codecs.open(filename=filename_in, mode='r', encoding=encode_in) as fi:
        #     data = fi.read()
        #     with open(filename_out, mode='w', encoding=encode_out) as fo:
        #         fo.write(data)
        #         fo.close()
        #输入表维度大小
        rows=2560
        cols=57
        data = pd.read_csv(filename_in, encoding="utf-8", header=None, nrows=rows, usecols=[i for i in range(cols)])
        # 调用模型计算脉搏类型预测结果
        result=predict.pulsePrediction(data.values)
        #print(data.dropna(axis=1).values)
        #print(data)
        formData['pulseType'] = result
        formData['fileName'] = ''
        # print(formData)
        newData = json.dumps(formData)  # json.dumps封装
        #print(newData)
        return render_template('diseasePrediction.html', newData=newData)
    
    
#用户通道数量      
@app.route('/find_channelNumber',methods=['GET','POST'])
def find_channelNumber():
    id = request.form.get('id')  # 用户id
    sql = "select count(*) from information_schema.COLUMNS where TABLE_SCHEMA='medical_dw' and table_name='ods_pulse_sig_" + str(
        id) + "'"
    cursor.execute(sql)  # 执行sql语句
    res = cursor.fetchall()  # 取数据
    json_data={}
    json_data['channelNumber'] = res[0][0]
    return json.dumps(json_data)


#根据id及通道编号获取用户通道数据
@app.route('/channel_data',methods=['GET','POST'])
def channel_data():
    id = request.form.get('id')  # 用户id
    num = request.form.get('num')  # 通道编号
    num=int(num)-1
    sql = "select `" + str(num) + "` from medical_dw.ods_pulse_sig_" + str(id)
    cursor.execute(sql)  # 执行sql语句
    res = cursor.fetchall()  # 取数据
    json_data = {}
    channel_data = []
    for i in res:
        channel_data.append(round(i[0],5))
    json_data["data"] = channel_data
    return json.dumps(json_data)


if __name__ == '__main__':
    app.run(debug=True)