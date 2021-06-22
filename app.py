# -*- coding:utf-8 -*-
from flask import Flask, render_template, request
import pymysql
import pandas as pd
import json
from utils import tool, load_data, ods_to_dwd
import os
from algorithm import predict
from sqlalchemy import create_engine
import pymssql

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
    engine = create_engine("mysql+pymysql://root:000000@58.199.160.140:3306/medical_dw?charset=utf8")
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

# 数据导入
@app.route('/dataimport', methods=["GET", "POST"])
def dataimport():
    data_source = request.form.get('data_source')   # 数据来源
    dept = request.form.get('dept')     # 科室
    # 确定表名和信息表字段
    patient_info_table_name = 'ods_kidney_info'
    pulse_table_name = 'ods_kidney_pulse_'
    col_names = ['id', 'sex', 'age', 'staging', 'serum_creatinine', 'eGFR', 'symptoms_type', 'tongue', 'pulse']
    ods_to_dwd_update_func = ods_to_dwd.ods_to_dwd_kidney
    if dept == 'liver':
        patient_info_table_name = 'ods_liver_info'
        pulse_table_name = 'ods_liver_pulse_'
        col_names = ['id', 'sex', 'age', 'ALT', 'symptoms_type', 'tongue', 'pulse']
        ods_to_dwd_update_func = ods_to_dwd.ods_to_dwd_liver
    elif dept == 'lung':
        patient_info_table_name = 'ods_lung_info'
        pulse_table_name = 'ods_lung_pulse_'
        col_names = ['id', 'sex', 'age', 'wm_diagnosis', 'lung_qi_deficiency', 'spleen_qi_deficiency', 'kidney_qi_deficiency',
                      'FEV1', 'FVC', 'FEV1%', 'FEV1/FVC', 'PEF', 'tongueA', 'tongueB', 'tongueC', 'pulseA', 'pulseB', 'pulseC', ]
        ods_to_dwd_update_func = ods_to_dwd.ods_to_dwd_lung

    patient_info_path = './tmp/patientinfo'
    pulse_path = './tmp/pulse'
    if data_source == 'local':              # 从本地导入数据到数据仓库
        patient_info_file = request.files.getlist("file")[0]  # 病例信息表
        patient_info_file_encoding = request.form.get('patient_info_file_encoding') # 病例信息表编码格式
        pulse_files = request.files.getlist("fileDir")  # 脉搏信号表,多个，数组存放
        pulse_file_encoding = request.form.get('pulse_file_encoding')  # 脉搏信号表编码格式
        try:
            # 清空临时文件目录下的所有内容
            load_data.clear_folder('./tmp/')
            # 保存到临时文件
            if patient_info_file is not None:
                patient_info_file.save(os.path.join(patient_info_path, 'patient_info.csv'))
            if pulse_files is not None:
                for pulse_file in pulse_files:
                    filename = pulse_file.filename
                    filename = filename[filename.index('/')+1:]
                    pulse_file.save(os.path.join(pulse_path, filename))
        except:
            print('Data uploading failed！')
            return 'Data uploading failed！'

        # 将数据导入数据仓库
        try:
            if dept == 'kidney':
                load_data.load_kidney_info_to_mysql(os.path.join(patient_info_path, 'patient_info.csv'), encoding=patient_info_file_encoding)
                load_data.load_kidney_pulse_to_mysql(pulse_path, encoding=pulse_file_encoding)
            elif dept == 'liver':
                load_data.load_liver_info_to_mysql(os.path.join(patient_info_path, 'patient_info.csv'), encoding=patient_info_file_encoding)
                load_data.load_liver_pulse_to_mysql(pulse_path, encoding=pulse_file_encoding)
            elif dept == 'lung':
                load_data.load_lung_info_to_mysql(os.path.join(patient_info_path, 'patient_info.csv'), encoding=patient_info_file_encoding)
                load_data.load_lung_pulse_to_mysql(pulse_path, encoding=pulse_file_encoding)
        except:
            print('Data importing fialed！')
            load_data.clear_folder('./tmp/')
            return 'Data importing fialed！'
        load_data.clear_folder('./tmp/')
    elif data_source in ['MySQL', 'SqlServer']:            # 从MySQL导入数据到数据仓库
        host = request.form.get('host')
        port = request.form.get('port')
        user = request.form.get('user')
        passwd = request.form.get('passwd')
        src_db = request.form.get('db')
        charset = request.form.get('charset')
        patient_info_table = request.form.get('patient_info_table')
        pulse_table_na_rule = request.form.get('pulse_table_na_rule')
        # print(host, port, user, passwd, db, charset, patient_info_table)
        try:
        # 连接数据库
            conn = ""
            if data_source == 'MySQL':
                conn = pymysql.connect(host=host, port=int(port), user=user, passwd=passwd, db=src_db, charset=charset)
            if data_source == 'SqlServer':
                conn = pymssql.connect(host=host, port=int(port), user=user, password=passwd, database=src_db, charset='GBK')
            src_cursor = conn.cursor()
            # 读取病例信息表
            sql = 'select * from ' + str(patient_info_table)
            src_cursor.execute(sql)
            query_result = src_cursor.fetchall()
            if len(query_result) == 0:
                print('Empty table!')
                return 'Empty table!'
            elif len(query_result[0]) != len(col_names):
                print('Columns do not match!')
                return 'Columns do not match!'
            pd_patient_info = pd.DataFrame(list(query_result), columns=col_names)
            # print(pd_patient_info)
            # 导入病例信息表到数据仓库
            # print(patient_info_table_name)
            pd_patient_info.to_sql(name=patient_info_table_name, con=engine, if_exists='append', index=False)

            # 读取并导入脉象数据
            for patient_id in pd_patient_info['id']:
                sql = 'select * from ' + pulse_table_name + patient_id
                try:
                    src_cursor.execute(sql)
                except:
                    print(patient_id, '脉博数据表不存在！')
                    continue
                query_result = src_cursor.fetchall()
                pd_pulse = pd.DataFrame(list(query_result))
                # print(pd_pulse)
                pd_pulse.to_sql(name=pulse_table_name+patient_id.lower(), con=engine, if_exists='replace', index=False)
        except:
            print('Data importing failed！')
            return 'Data importing failed！'

    ods_to_dwd_update_func()
    return 'Data importing succeed！'


@app.route('/fileInput', methods=["GET", "POST"])
def fileInpute():
    return render_template('fileInput.html')

# 肾科病人信息统计
@app.route('/datastatistic', methods=["GET", "POST"])
def kidney_statistic():
    if request.method == "GET":
        # 从数据库获取病人信息表
        try:
            cursor.execute("SELECT sex, age, serum_creatinine, eGFR, symptoms_type FROM dwd_kidney_info;")
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
        # print(gender, symptoms_type, min_age, max_age, min_sc_value, max_sc_value, min_eGFR, max_eGFR)

        sql = "SELECT sex, age, serum_creatinine, eGFR, symptoms_type FROM dwd_kidney_info WHERE id IS NOT NULL"
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
            return '从服务器获取数据失败'
        query_result = cursor.fetchall()
        col_names = pd.DataFrame(list(cursor.description)).iloc[:, 0].tolist()
        pd_patient_info = pd.DataFrame(list(query_result), columns=col_names)
        # print(pd_patient_info)

        data = tool.get_statistic_info(pd_patient_info)

        data_json = json.dumps(data)
        return data_json


@app.route('/statistic_kidney',methods=['GET', 'POST'])
def statistic_detail_kidney():
    return render_template('statistic_kidney.html')


# 肝科病人信息统计
@app.route('/liver_statistic', methods=["GET", "POST"])
def liver_statistic():
    if request.method == "GET":
        # 从数据库获取病人信息表
        try:
            cursor.execute("SELECT sex, age, ALT, symptoms_type FROM dwd_liver_info;")
        except:
            print('从服务器获取数据失败')
            return '从服务器获取数据失败'
        query_result = cursor.fetchall()
        col_names = pd.DataFrame(list(cursor.description)).iloc[:,0].tolist()
        pd_liver_info = pd.DataFrame(list(query_result), columns=col_names)

        data = tool.get_liver_statistic_info(pd_liver_info)

        data_json = json.dumps(data)
        return data_json
    elif request.method == "POST":
        gender = request.form.get('gender')
        min_age = request.form.get('min_age')
        max_age = request.form.get('max_age')
        min_ALT = request.form.get('min_ALT')
        max_ALT = request.form.get('max_ALT')
        symptoms_type = request.form.get('symptoms_type')
        print(gender, symptoms_type, min_age, max_age, min_ALT, max_ALT)

        sql = "SELECT sex, age, ALT, symptoms_type FROM dwd_liver_info WHERE id IS NOT NULL"
        t = [None, '', 'all']
        gender_dict = {'1':'2', '2':'1'}
        if gender not in t:
            sql = sql + " AND sex=" + gender_dict[str(gender)]
        if min_age not in t:
            sql = sql + " AND age>=" + str(min_age)
        if max_age not in t:
            sql = sql + " AND age<=" + str(max_age)
        if min_ALT not in t:
            sql = sql + " AND ALT>=" + str(min_ALT)
        if max_ALT not in t:
            sql = sql + " AND ALT<=" + str(max_ALT)
        if symptoms_type not in t:
            sql = sql + " AND symptoms_type=" + str(symptoms_type)
        # print(sql)

        # 从数据库获取病人信息表
        try:
            cursor.execute(sql)
        except:
            print('从服务器获取数据失败')
            return '从服务器获取数据失败'
        query_result = cursor.fetchall()
        col_names = pd.DataFrame(list(cursor.description)).iloc[:, 0].tolist()
        pd_liver_info = pd.DataFrame(list(query_result), columns=col_names)
        # print(pd_liver_info)

        data = tool.get_liver_statistic_info(pd_liver_info)
        # print(data)

        data_json = json.dumps(data)
        return data_json

@app.route('/statistic_liver',methods=['GET', 'POST'])
def statistic_detail_liver():
    return render_template('statistic_liver.html')

# 肺科病人信息统计
@app.route('/lung_statistic', methods=["GET", "POST"])
def lung_statistic():
    if request.method == "GET":
        # 从数据库获取病人信息表
        try:
            cursor.execute("SELECT sex, age, Lung_qi_deficiency, spleen_qi_deficiency, kidney_qi_deficiency FROM dwd_lung_info;")
        except:
            print('从服务器获取数据失败')
            return '从服务器获取数据失败'
        query_result = cursor.fetchall()
        col_names = pd.DataFrame(list(cursor.description)).iloc[:,0].tolist()
        pd_lung_info = pd.DataFrame(list(query_result), columns=col_names)
        # print(pd_lung_info)

        data = tool.get_lung_statistic_info(pd_lung_info)
        # print(data)

        data_json = json.dumps(data)
        return data_json
    elif request.method == "POST":
        gender = request.form.get('gender')
        min_age = request.form.get('min_age')
        max_age = request.form.get('max_age')
        Lung_qi_deficiency = request.form.get('Lung_qi_deficiency')
        spleen_qi_deficiency = request.form.get('spleen_qi_deficiency')
        kidney_qi_deficiency = request.form.get('kidney_qi_deficiency')
        # print(gender, min_age, max_age, Lung_qi_deficiency, spleen_qi_deficiency, kidney_qi_deficiency)

        sql = "SELECT sex, age, Lung_qi_deficiency, spleen_qi_deficiency, kidney_qi_deficiency FROM dwd_lung_info WHERE id IS NOT NULL"
        t = [None, '', 'all']
        if gender not in t:
            sql = sql + " AND sex=" + str(gender)
        if min_age not in t:
            sql = sql + " AND age>=" + str(min_age)
        if max_age not in t:
            sql = sql + " AND age<=" + str(max_age)
        if Lung_qi_deficiency not in t:
            sql = sql + " AND Lung_qi_deficiency=" + str(Lung_qi_deficiency)
        if spleen_qi_deficiency not in t:
            sql = sql + " AND spleen_qi_deficiency=" + str(spleen_qi_deficiency)
        if kidney_qi_deficiency not in t:
            sql = sql + " AND kidney_qi_deficiency=" + str(kidney_qi_deficiency)
        # print(sql)

        # 从数据库获取病人信息表
        try:
            cursor.execute(sql)
        except:
            print('从服务器获取数据失败')
            return '从服务器获取数据失败'
        query_result = cursor.fetchall()
        col_names = pd.DataFrame(list(cursor.description)).iloc[:, 0].tolist()
        pd_lung_info = pd.DataFrame(list(query_result), columns=col_names)
        # print(pd_lung_info)

        data = tool.get_lung_statistic_info(pd_lung_info)
        # print(data)

        data_json = json.dumps(data)
        return data_json
@app.route('/statistic_lung',methods=['GET', 'POST'])
def statistic_detail_lung():
    return render_template('statistic_lung.html')

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
        formData={'sex': '男', 'userage': '', 'stage': '', 'bloodCreatinine': '', 'egfr': '', 'fileName': '', 'pulseType': '', 'fileRead': 'success'}
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
        # filename_out = './files/pulseFileUTF.csv'

        # 输入文件的编码类型
        encode_in = 'utf-16 le'
        #输入表维度大小
        rows=2560
        cols=57
        formData['fileRead'] = 'success'
        try:
            data = pd.read_csv(filename_in, encoding=encode_in, header=None, nrows=rows,usecols=[i for i in range(cols)])
            # 调用模型计算脉搏类型预测结果
            result = predict.pulsePrediction(data.values)
            formData['pulseType'] = result
            formData['fileName'] = ''
        except UnicodeDecodeError as e:
            data = pd.read_csv(filename_in, encoding='utf-8', header=None, nrows=rows,usecols=[i for i in range(cols)])
            # 调用模型计算脉搏类型预测结果
            result = predict.pulsePrediction(data.values)
            formData['pulseType'] = result
            formData['fileName'] = ''
        except ValueError as e:
            data = pd.read_csv(filename_in, encoding='utf-8', header=None, nrows=rows,usecols=[i for i in range(cols)])
            # 调用模型计算脉搏类型预测结果
            result = predict.pulsePrediction(data.values)
            formData['pulseType'] = result
            formData['fileName'] = ''
        else:
            formData = {'sex': '男', 'userage': '', 'stage': '', 'bloodCreatinine': '', 'egfr': '', 'fileName': '',
                        'pulseType': '', 'fileRead': 'fail'}

        newData = json.dumps(formData)  # json.dumps封装
        return newData
    
@app.route('/pulsePrediction_accuracy', methods=["POST"])
def pulsePrediction_accuracy():
    # 获取前端请求的数据
    selectTestNum = request.form.get('selectTestNum')
    testNum=int(selectTestNum)
    totalNum=857
    # 调用模型验证测试结果(读取文件速度太慢，直接写死用读好的数据)
    idSet,predicted,labels,correct,total,accuracy = predict.mulPulsePrediction(testNum,totalNum)
    # 方案一：沉细-0 细-1 弦-2 弦细-3 滑-4 濡-5
    pulseType = ['沉细', '细', '弦', '弦细', '滑', '濡']
    predictType=[]
    labelType=[]
    for index in range(testNum):
        predictType.append(pulseType[predicted[index]])
        labelType.append(pulseType[labels[index]])
    formData = {}
    formData['testNum']=str(testNum)
    formData['num_pos']=correct
    formData['num_neg']=total-correct
    formData['accuracy']=accuracy
    formData['predictType']=predictType
    formData['labelType']=labelType
    formData['idSet']=idSet
    newData = json.dumps(formData)  # json.dumps封装
    return newData    
    
#用户通道数量      
@app.route('/find_channelNumber',methods=['GET','POST'])
def find_channelNumber():
    id = request.form.get('id')  # 用户id
    type=request.form.get('type')
    if (type=='kidney' or type=='liver'):
        sql = "select count(*) from information_schema.COLUMNS where TABLE_SCHEMA='medical_dw' and table_name='ods_"+type+"_pulse_" + str(
        id) + "'"
    elif (type=='lung'):
        sql = "select count(*) from information_schema.COLUMNS where TABLE_SCHEMA='medical_dw' and table_name='ods_lung_pulse_" + str(
            id).casefold() + "'"
    cursor.execute(sql)  # 执行sql语句
    res = cursor.fetchall()  # 取数据
    json_data={}
    json_data['channelNumber'] = res[0][0]
    print(json_data['channelNumber'])
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
    pi_qi_xu = request.form.get('pi_qi_xu')  # 脾气虚
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

@app.route('/tongue_data',methods=['GET','POST'])
def tongue_data():

    def return_img_stream(img_local_path):
        """
        工具函数:
        获取本地图片流
        :param img_local_path:文件单张图片的本地绝对路径
        :return: 图片流
        """
        import base64
        img_stream = ''
        with open(img_local_path, 'rb') as img_f:
            img_stream = img_f.read()
            img_stream = base64.b64encode(img_stream).decode()
        return img_stream
    id=request.form.get('id')
    patient= request.form.get('patient')
    cur_path_raw='static/data/tongueimage/' + patient + '/' + id + '.bmp'
    json_data = {}
    if(os.path.exists(cur_path_raw)):
        img_stream=return_img_stream(cur_path_raw)
        json_data['tongue_data'] = img_stream
    else:
        json_data['tongue_data'] = 'None'
    return json_data


if __name__ == '__main__':
    app.run(debug=True)
