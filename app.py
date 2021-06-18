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


@app.route('/statistic_detail',methods=['GET', 'POST'])
def statistic_detail():
    if request.method == "POST":
        gender = request.form.get('gender')
        min_age = request.form.get('min_age')
        max_age = request.form.get('max_age')
        min_sc_value = request.form.get('min_sc_value')
        max_sc_value = request.form.get('max_sc_value')
        min_eGFR = request.form.get('min_eGFR')
        max_eGFR = request.form.get('max_eGFR')
        symptoms_type = request.form.get('symptoms_type')
        print(gender, symptoms_type, min_age, max_age, min_sc_value, max_sc_value, min_eGFR, max_eGFR)

        sql = "SELECT sex, age, serum_creatinine, eGFR, symptoms_type FROM dwd_patient_info WHERE id IS NOT NULL"
        t = [None, '', 'all']
        if gender not in t:
            sql = sql + " AND sex=" + str(gender)
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
        if symptoms_type not in t:
            sql = sql + " AND symptoms_type=" + str(symptoms_type)
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

    elif request.method == "GET":
        return render_template('statistic_detail.html',data_json=0)

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
    sql = "select * from dwd_kidney_info where 1=1 "
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
    sql_COLUMN_NAME = "select COLUMN_NAME from INFORMATION_SCHEMA.Columns where table_name = 'dwd_kidney_info' and " \
                      "table_schema = 'medical_dw' ORDER BY ordinal_position"
    cursor.execute(sql_COLUMN_NAME)  
    column_names = cursor.fetchall()  # 获取列名字数据
    for result in data:
        one_person = {}
        for i in range(len(column_names)):
            one_person[column_names[i][0]] = str(result[i])
        result_data.append(one_person)
        
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
    type=request.form.get('type')
    if (type=='kidney' or type=='liver'):
        sql = "select count(*) from information_schema.COLUMNS where TABLE_SCHEMA='medical_dw' and table_name='ods_"+type+"_pulse__" + str(
        id) + "'"
    elif (type=='lung'):
        sql = "select count(*) from information_schema.COLUMNS where TABLE_SCHEMA='medical_dw' and table_name='ods_lung_pulse_" + str(
            id).casefold() + "'"
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
    type = request.form.get('type')
    if (type == 'kidney' or type == 'liver'):
        sql = "select `" + str(num) + "` from medical_dw.ods_"+type+"_pulse_" + str(id)
    elif (type == 'lung'):
        sql = "select `" + str(num) + "` from medical_dw.ods_lung_pulse_" + str(id).casefold()
    cursor.execute(sql)  # 执行sql语句
    res = cursor.fetchall()  # 取数据
    json_data = {}
    channel_data = []
    for i in res:
        channel_data.append(round(i[0],5))
    json_data["data"] = channel_data
    return json.dumps(json_data)
    
    
#查询肺病人的信息
@app.route('/lung_patient_info',methods=['POST'])
def lung_patient_info():
    page = request.form.get('page')  # 页数
    limit = request.form.get('limit')  # 每页显示的数量
    if page is None or page=="":
        page=1
    if limit is None or limit=="":
        limit=10
    id = request.form.get('id')  # 编号
    sex = request.form.get('sex')  # 性别
    age = json.loads(request.form.get('age'))  # 年龄
    wm_diagnosis = request.form.get('wm_diagnosis')  # 西医诊断
    fei_qi_xu = request.form.get('fei_qi_xu')  # 肺气虚
    pi_qi_xu = request.form.get('wm_diagnosis')  # 脾气虚
    sheng_qi_xu = request.form.get('sheng_qi_xu')  # 肾气虚
    FEV1 = json.loads(request.form.get('FEV1'))  # 年龄
    FVC = json.loads(request.form.get('FVC'))  # 年龄
    FEV11 = json.loads(request.form.get('FEV1%'))  # 年龄
    FEV2 = json.loads(request.form.get('FEV1/FVC'))  # FEV1 / FVC改值
    PEF = json.loads(request.form.get('PEF'))
    tongue = request.form.get('tongue')  # 舌象
    pulse = request.form.get('pulse')  # 脉象
    sql = "select * from dwd_lung_info where 1=1 "
    print(sql)
    if id != "":
        sql += "and id='" + str(id) + "'"
    if sex != "":
        sql += "and sex='" + str(sex) + "'"
    if age != "" and age[0] != "":
        sql += "and age>='" + str(age[0]) + "'"
    if age != "" and age[1] != "":
        sql += "and age<='" + str(age[1]) + "'"
    if wm_diagnosis != "":
        sql += "and wm_diagnosis like '" + "%" + str(wm_diagnosis) + "%" + "'"
    if fei_qi_xu != "":
        sql += "and Lung_qi_deficiency='" + str(fei_qi_xu) + "'"
    if pi_qi_xu != "":
        sql += "and spleen_qi_deficiency='" + str(pi_qi_xu) + "'"
    if sheng_qi_xu != "":
        sql += "and kidney_qi_deficiency='" + str(sheng_qi_xu) + "'"
    if FEV1 != "" and FEV1[0] != "":
        sql += "and FEV1>='" + str(FEV1[0]) + "'"
    if FEV1 != "" and FEV1[1] != "":
        sql += "and FEV1<='" + str(FEV1[1]) + "'"
    if FVC != "" and FVC[0] != "":
        sql += "and FVC>='" + str(FVC[0]) + "'"
    if FVC != "" and FVC[1] != "":
        sql += "and FVC<='" + str(FVC[1]) + "'"
    if FEV11 != "" and FEV11[0] != "":
        sql += "and \'FEV1%\'>='" + str(FEV11[0]) + "'"
    if FEV11 != "" and FEV11[1] != "":
        sql += "and \'FEV1%\'<='" + str(FEV11[1]) + "'"
    if FEV2 != "" and FEV2[0] != "":
        sql += "and \'FEV1/FVC>=\''" + str(FEV2[0]) + "'"
    if FEV2 != "" and FEV2[1] != "":
        sql += "and \'FEV1/FVC<=\''" + str(FEV2[1]) + "'"
    if PEF != "" and PEF[0] != "":
        sql += "and PEF>='" + str(PEF[0]) + "'"
    if PEF != "" and PEF[1] != "":
        sql += "and PEF<='" + str(PEF[1]) + "'"
    if tongue != "":
        sql += "and tongue like '" + "%" + str(tongue) + "%" + "'"
    if pulse != "":
        sql += "and pulse like '" + "%" + str(pulse) + "%" + "'"
    offset = (int(page) - 1) * int(limit)  # 起始行
    cursor.execute(sql)
    total_data = cursor.fetchall()  # 所有满足条件的数据
    sql += "limit " + str(offset) + ',' + str(limit)
    cursor.execute(sql)  # 执行sql语句
    data = cursor.fetchall()  # 获取数据
    json_data = {}
    result_data = []

    sql_COLUMN_NAME = "select COLUMN_NAME from INFORMATION_SCHEMA.Columns where table_name = 'dwd_lung_info' and " \
                      "table_schema = 'medical_dw' ORDER BY ordinal_position"
    cursor.execute(sql_COLUMN_NAME)  # 执行sql语句
    column_names = cursor.fetchall()  # 获取数据

    for result in data:
        one_person = {}
        for i in range(len(column_names)):
            one_person[column_names[i][0]] = str(result[i])
        result_data.append(one_person)
    json_data['total'] = len(total_data)
    json_data['data'] = result_data
    json_data = json.dumps(json_data, ensure_ascii=False)
    return json_data
    
    
@app.route('/liver_patient_info',methods=['POST'])
def liver_patient_info():
    page = request.form.get('page')  # 页数
    limit = request.form.get('limit')  # 每页显示的数量
    if page is None or page == "":
        page = 1
    if limit is None or limit == "":
        limit = 10
    id = request.form.get('id')  # 编号
    sex = request.form.get('sex')  # 性别
    age = json.loads(request.form.get('age'))  # 年龄
    symptoms_type = request.form.get('symptoms_type')#症型
    ALT = json.loads(request.form.get('ALT'))
    tongue = request.form.get('tongue')  # 舌象
    pulse = request.form.get('pulse')  # 脉象
    sql = "select * from dwd_liver_info where 1=1 "
    if id != "":
        sql += "and id='" + str(id) + "'"
    if sex != "":
        sql += "and sex='" + str(sex) + "'"
    if age != "" and age[0] != "":
        sql += "and age>'" + str(age[0]) + "'"
    if age != "" and age[1] != "":
        sql += "and age<'" + str(age[1]) + "'"
    if ALT != "" and ALT[0] != "":
        sql += "and ALT>'" + str(ALT[0]) + "'"
    if ALT != "" and ALT[1] != "":
        sql += "and ALT<'" + str(ALT[1]) + "'"
    if symptoms_type != "":
        sql += "and symptoms_type='" + str(symptoms_type) + "'"
    if tongue != "":
        sql += "and tongue like '" + "%" + str(tongue) + "%" + "'"
    if pulse != "":
        sql += "and pulse like '" + "%" + str(pulse) + "%" + "'"
    offset = (int(page) - 1) * int(limit)  # 起始行
    cursor.execute(sql)
    total_data = cursor.fetchall()  # 所有满足条件的数据
    sql += "limit " + str(offset) + ',' + str(limit)
    cursor.execute(sql)  # 执行sql语句
    data = cursor.fetchall()  # 获取数据
    json_data = {}
    result_data = []
    sql_COLUMN_NAME = "select COLUMN_NAME from INFORMATION_SCHEMA.Columns where table_name = 'dwd_liver_info' and " \
                      "table_schema = 'medical_dw' ORDER BY ordinal_position"
    cursor.execute(sql_COLUMN_NAME)  # 执行sql语句
    column_names = cursor.fetchall()  # 获取数据
    for result in data:
        one_person = {}
        for i in range(len(column_names)):
            one_person[column_names[i][0]] = str(result[i])
        result_data.append(one_person)
    json_data['total'] = len(total_data)
    json_data['data'] = result_data
    json_data = json.dumps(json_data, ensure_ascii=False)
    return json_data




if __name__ == '__main__':
    app.run(debug=True)