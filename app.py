# -*- coding:utf-8 -*-
import decimal

from flask import Flask, render_template, request
import pymysql
import pandas as pd
import json
from utils import tool, load_data, ods_to_dwd
import os
from algorithm import predict
from algorithm import kindney_symptom_predict, liver_symptom_predict, lung_symptom_predict
from algorithm import tongue_color_predict
from sqlalchemy import create_engine
import pymssql
from dbutils.pooled_db import PooledDB

# 连接数据库
try:
    POOL = PooledDB(
        creator=pymysql,  # 使用链接数据库的模块
        maxconnections=6,  # 连接池允许的最大连接数，0和None表示不限制连接数
        mincached=2,  # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
        maxcached=5,  # 链接池中最多闲置的链接，0和None不限制
        maxshared=3,
        # 链接池中最多共享的链接数量，0和None表示全部共享。PS: 无用，因为pymysql和MySQLdb等模块的 threadsafety都为1，所有值无论设置为多少，_maxcached永远为0，所以永远是所有链接都共享。
        blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
        maxusage=None,  # 一个链接最多被重复使用的次数，None表示无限制
        setsession=[],  # 开始会话前执行的命令列表。如：["set datestyle to ...", "set time zone ..."]
        ping=0,
        # ping MySQL服务端，检查是否服务可用。# 如：0 = None = never, 1 = default = whenever it is requested, 2 = when a cursor is created, 4 = when a query is executed, 7 = always
        host='58.199.160.140',
        port=3306,
        user='root',
        password='000000',
        database='medical_dw',
        charset='utf8'
    )
    engine = create_engine("mysql+pymysql://root:000000@58.199.160.140:3306/medical_dw?charset=utf8")
except:
    print('数据库连接失败！')
    exit(0)


app = Flask(__name__)
app.secret_key = '000000'


@app.route('/')
def hello_world():
    return render_template('home.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    user = request.form.get('user')
    password = request.form.get('password')
    if user == 'test' and password == 'lib615604':
        return '验证通过'
    else:
        return '用户名或密码错误'

@app.route('/mainPage')
def main_page():
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
            # 导入病例信息表到数据仓库
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
    # 本地数据导入文件格式
    kidneyinfo = tongue_color_predict.img_stream("static/image/importexamples/kidneyinfo.jpg")   #肾科病人信息表
    liverinfo = tongue_color_predict.img_stream("static/image/importexamples/liverinfo.jpg")   #肝科病人信息表
    lunginfo = tongue_color_predict.img_stream("static/image/importexamples/lunginfo.jpg")   #肺科病人信息表
    # 病人脉象文件目录
    pulsefiles = tongue_color_predict.img_stream("static/image/importexamples/pulsefiles.jpg")   #脉象文件
    data = {
        'kidneyinfo':kidneyinfo,
        'liverinfo':liverinfo,
        'lunginfo':lunginfo,
        'pulsefiles':pulsefiles
    }
    data_json = json.dumps(data)
    return render_template('fileInput.html', data_json=data_json)

# 肾科病人信息统计
@app.route('/datastatistic', methods=["GET", "POST"])
def kidney_statistic():
    if request.method == "GET":
        # 从数据库获取病人信息表
        try:
            conn = POOL.connection(shareable=False)
            cursor1 = conn.cursor()
            cursor1.execute("SELECT sex, age, serum_creatinine, eGFR, symptoms_type FROM dwd_kidney_info;")
        except:
            print('从服务器获取数据失败')
            return 0
        query_result = cursor1.fetchall()
        col_names = pd.DataFrame(list(cursor1.description)).iloc[:,0].tolist()
        pd_patient_info = pd.DataFrame(list(query_result), columns=col_names)

        data = tool.get_statistic_info(pd_patient_info)

        data_json = json.dumps(data)
        cursor1.close()
        conn.close()
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

        # 从数据库获取病人信息表
        try:
            conn = POOL.connection(shareable=False)
            cursor1 = conn.cursor()
            cursor1.execute(sql)
        except:
            print('从服务器获取数据失败')
            return '从服务器获取数据失败'
        query_result = cursor1.fetchall()
        col_names = pd.DataFrame(list(cursor1.description)).iloc[:, 0].tolist()
        pd_patient_info = pd.DataFrame(list(query_result), columns=col_names)

        data = tool.get_statistic_info(pd_patient_info)

        cursor1.close()
        conn.close()

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
            conn = POOL.connection(shareable=False)
            cursor1 = conn.cursor()
            cursor1.execute("SELECT sex, age, ALT, symptoms_type FROM dwd_liver_info;")
        except:
            print('从服务器获取数据失败')
            return '从服务器获取数据失败'
        query_result = cursor1.fetchall()
        col_names = pd.DataFrame(list(cursor1.description)).iloc[:,0].tolist()
        pd_liver_info = pd.DataFrame(list(query_result), columns=col_names)

        data = tool.get_liver_statistic_info(pd_liver_info)

        cursor1.close()
        conn.close()

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
            conn = POOL.connection(shareable=False)
            cursor1 = conn.cursor()
            cursor1.execute(sql)
        except:
            print('从服务器获取数据失败')
            return '从服务器获取数据失败'
        query_result = cursor1.fetchall()
        col_names = pd.DataFrame(list(cursor1.description)).iloc[:, 0].tolist()
        pd_liver_info = pd.DataFrame(list(query_result), columns=col_names)
        # print(pd_liver_info)

        data = tool.get_liver_statistic_info(pd_liver_info)

        cursor1.close()
        conn.close()

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
            conn = POOL.connection(shareable=False)
            cursor1 = conn.cursor()
            cursor1.execute("SELECT sex, age, Lung_qi_deficiency, spleen_qi_deficiency, kidney_qi_deficiency FROM dwd_lung_info;")
        except:
            print('从服务器获取数据失败')
            return '从服务器获取数据失败'
        query_result = cursor1.fetchall()
        col_names = pd.DataFrame(list(cursor1.description)).iloc[:,0].tolist()
        pd_lung_info = pd.DataFrame(list(query_result), columns=col_names)

        cursor1.close()
        conn.close()

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
            conn = POOL.connection(shareable=False)
            cursor1 = conn.cursor()
            cursor1.execute(sql)
        except:
            print('从服务器获取数据失败')
            return '从服务器获取数据失败'
        query_result = cursor1.fetchall()
        col_names = pd.DataFrame(list(cursor1.description)).iloc[:, 0].tolist()
        pd_lung_info = pd.DataFrame(list(query_result), columns=col_names)

        cursor1.close()
        conn.close()

        data = tool.get_lung_statistic_info(pd_lung_info)

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
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()
    sql+="limit "+str(offset)+','+str(limit)
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

    cursor.close()
    conn.close()
        
    json_data["code"] = str(0)
    json_data['total'] = len(totalQueryData)
    json_data['data'] = result_data
    json_data = json.dumps(json_data, ensure_ascii=False)
    return json_data

#获取预测序列的用户信息（查三科表，脉象）
@app.route('/patient_info_of_pulse_by_id', methods=['POST'])
def patient_info_of_pulse_by_id():
    page = request.form.get('page')  # 页数
    limit = request.form.get('limit')  # 每页显示的数量
    if page is None:
        page = 1
    if limit is None:
        limit = 1
    # 获取前端请求的数据
    idSet = json.loads(request.form.get('idSet'))
    predictType = json.loads(request.form.get('predictType'))
    labelType = json.loads(request.form.get('labelType'))
    json_data = {}
    result_data = []
    # 填充返回前端table的json数据（肾科）
    idStr="'"+",".join(idSet)+"'"
    sql = "select id,sex,age,tongue,pulse from dwd_kidney_info where FIND_IN_SET(id,"+idStr+") order by FIND_IN_SET(id,"+idStr+")"
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()

    # 填充返回前端table的json数据
    for data in totalQueryData:
        temp_data = {}
        temp_data['index'] = idSet.index(data[0])
        temp_data['id'] = data[0]
        if data[1] == '1':
            temp_data['sex'] = '男'
        elif data[1] == '2':
            temp_data['sex'] = '女'
        temp_data['age'] = data[2]
        temp_data['tongue'] = data[3]
        temp_data['pulse'] = data[4]
        temp_data['labelType'] = labelType[idSet.index(data[0])]
        temp_data['predictType'] = predictType[idSet.index(data[0])]
        result_data.append(temp_data)

    # 填充返回前端table的json数据（肝科）
    sql = "select id,sex,age,tongue,pulse from dwd_liver_info where FIND_IN_SET(id," + idStr + ") order by FIND_IN_SET(id," + idStr + ")"
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()
    # 填充返回前端table的json数据
    for data in totalQueryData:
        temp_data = {}
        temp_data['index'] = idSet.index(data[0])
        temp_data['id'] = data[0]
        if data[1] == '1':
            temp_data['sex'] = '女'
        elif data[1] == '2':
            temp_data['sex'] = '男'
        temp_data['age'] = data[2]
        temp_data['tongue'] = data[3]
        temp_data['pulse'] = data[4]
        temp_data['labelType'] = labelType[idSet.index(data[0])]
        temp_data['predictType'] = predictType[idSet.index(data[0])]
        result_data.append(temp_data)

    # 填充返回前端table的json数据（肺科）
    sql = "select id,sex,age,tongue,pulse from dwd_lung_info where FIND_IN_SET(id," + idStr + ") order by FIND_IN_SET(id," + idStr + ")"
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()
    # 填充返回前端table的json数据
    for data in totalQueryData:
        temp_data = {}
        temp_data['index'] = idSet.index(data[0])
        temp_data['id'] = data[0]
        if data[1] == '1':
            temp_data['sex'] = '女'
        elif data[1] == '2':
            temp_data['sex'] = '男'
        temp_data['age'] = data[2]
        temp_data['tongue'] = data[3]
        temp_data['pulse'] = data[4]
        temp_data['labelType'] = labelType[idSet.index(data[0])]
        temp_data['predictType'] = predictType[idSet.index(data[0])]
        result_data.append(temp_data)

    cursor.close()
    conn.close()

    result_data.sort(key=lambda s: s["index"])#要根据原来的（折线）序号index进行排序
    json_data['code'] = str(0)
    json_data['msg'] = ''
    json_data['total'] = len(result_data)
    offset = (int(page) - 1) * int(limit)  # 起始行
    endset = offset + int(limit)
    if endset > len(result_data):
        endset = len(result_data)
    json_data['data'] = result_data[offset:endset]
    json_data = json.dumps(json_data)
    return json_data

#获取预测序列的用户信息（查肾科病表）
@app.route('/patient_info_of_kindney_by_id', methods=['POST'])
def patient_info_of_kindney_by_id():
    page = request.form.get('page')  # 页数
    limit = request.form.get('limit')  # 每页显示的数量
    if page is None:
        page = 1
    if limit is None:
        limit = 1
    # 获取前端请求的数据
    idSet = json.loads(request.form.get('idSet'))
    predictType = json.loads(request.form.get('predictType'))
    json_data = {}
    result_data = []
    # 填充返回前端table的json数据
    idStr="'"+",".join(idSet)+"'"
    sql = "select id,sex,age,serum_creatinine,eGFR,tongue,pulse,symptoms_type from dwd_kidney_info where FIND_IN_SET(id,"+idStr+") order by FIND_IN_SET(id,"+idStr+")"
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()
    # 填充返回前端table的json数据
    for data in totalQueryData:
        temp_data = {}
        temp_data['index'] = idSet.index(data[0])
        temp_data['id'] = data[0]
        if data[1] == '1':
            temp_data['sex'] = '男'
        elif data[1] == '2':
            temp_data['sex'] = '女'
        temp_data['age'] = data[2]
        temp_data['serum_creatinine'] = str(data[3])
        temp_data['eGFR'] = str(data[4])
        temp_data['tongue'] = data[5]
        temp_data['pulse'] = data[6]
        if data[7] == '1':
            temp_data['symptoms_type'] = '肾阳虚'
        elif data[7] == '2':
            temp_data['symptoms_type'] = '肾阴虚'
        temp_data['predictType'] = predictType[idSet.index(data[0])]
        result_data.append(temp_data)

    cursor.close()
    conn.close()

    json_data['code'] = str(0)
    json_data['msg'] = ''
    json_data['total'] = len(result_data)
    offset = (int(page) - 1) * int(limit)  # 起始行
    endset = offset + int(limit)
    if endset > len(result_data):
        endset = len(result_data)
    json_data['data'] = result_data[offset:endset]
    json_data = json.dumps(json_data)
    return json_data

#获取预测序列的用户信息（查肝科病表）
@app.route('/patient_info_of_liver_by_id', methods=['POST'])
def patient_info_of_liver_by_id():
    page = request.form.get('page')  # 页数
    limit = request.form.get('limit')  # 每页显示的数量
    if page is None:
        page = 1
    if limit is None:
        limit = 1
    # 获取前端请求的数据
    idSet = json.loads(request.form.get('idSet'))
    predictType = json.loads(request.form.get('predictType'))
    json_data = {}
    result_data = []
    # 填充返回前端table的json数据
    idStr="'"+",".join(idSet)+"'"
    sql = "select id,sex,age,ALT,tongue,pulse,symptoms_type from dwd_liver_info where FIND_IN_SET(id,"+idStr+") order by FIND_IN_SET(id,"+idStr+")"
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()
    # 填充返回前端table的json数据
    for data in totalQueryData:
        temp_data = {}
        temp_data['index'] = idSet.index(data[0])
        temp_data['id'] = data[0]
        if data[1] == '1':
            temp_data['sex'] = '女'
        elif data[1] == '2':
            temp_data['sex'] = '男'
        temp_data['age'] = data[2]
        temp_data['ALT'] = str(data[3])
        temp_data['tongue'] = data[4]
        temp_data['pulse'] = data[5]
        if data[6] == '1':
            temp_data['symptoms_type'] = '肝胆湿热症'
        elif data[6] == '2':
            temp_data['symptoms_type'] = '肝郁脾虚症'
        temp_data['predictType'] = predictType[idSet.index(data[0])]
        result_data.append(temp_data)
    json_data['code'] = str(0)
    json_data['msg'] = ''
    json_data['total'] = len(result_data)
    offset = (int(page) - 1) * int(limit)  # 起始行
    endset = offset + int(limit)
    if endset > len(result_data):
        endset = len(result_data)

    cursor.close()
    conn.close()

    json_data['data'] = result_data[offset:endset]
    json_data = json.dumps(json_data)
    return json_data

#获取预测序列的用户信息（查肺科病表）
@app.route('/patient_info_of_lung_by_id', methods=['POST'])
def patient_info_of_lung_by_id():
    page = request.form.get('page')  # 页数
    limit = request.form.get('limit')  # 每页显示的数量
    if page is None:
        page = 1
    if limit is None:
        limit = 1
    # 获取前端请求的数据
    idSet = json.loads(request.form.get('idSet'))
    lungPredictType = json.loads(request.form.get('lungPredictType'))
    spleenPredictType = json.loads(request.form.get('spleenPredictType'))
    kidneyPredictType = json.loads(request.form.get('kidneyPredictType'))
    json_data = {}
    result_data = []
    # 填充返回前端table的json数据
    idStr="'"+",".join(idSet)+"'"
    # idStr="'K0001,K0002,K0003,K0004,K0005,K0006,K0007,K0008,K0009,K0010,K0011'"
    sql = "select id,sex,age,FEV1,FVC,`FEV1%`,FEV1/FVC,PEF,tongue,pulse,Wesmedicine_diagnosis,Lung_qi_deficiency,spleen_qi_deficiency,kidney_qi_deficiency from dwd_lung_info where FIND_IN_SET(id,"+idStr+") order by FIND_IN_SET(id,"+idStr+")"
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()
    # 填充返回前端table的json数据
    for data in totalQueryData:
        temp_data = {}
        temp_data['index'] = idSet.index(data[0])
        temp_data['id'] = data[0]
        if data[1] == '1':
            temp_data['sex'] = '女'
        elif data[1] == '2':
            temp_data['sex'] = '男'
        temp_data['age'] = data[2]
        temp_data['FEV1'] = str(data[3])
        temp_data['FVC'] = str(data[4])
        temp_data['FEV1%'] = str(data[5])
        temp_data['FEV1/FVC'] = str(data[6])
        temp_data['PEF'] = data[7]
        temp_data['tongue'] = data[8]
        temp_data['pulse'] = data[9]
        temp_data['wd_diagnosis'] = data[10]
        if data[11] == '1':
            temp_data['Lung_qi_deficiency'] = '有肺气虚'
        elif data[11] == '0':
            temp_data['Lung_qi_deficiency'] = '无肺气虚'
        temp_data['lungPredictType'] = lungPredictType[idSet.index(data[0])]
        if data[12] == '1':
            temp_data['spleen_qi_deficiency'] = '有脾气虚'
        elif data[12] == '0':
            temp_data['spleen_qi_deficiency'] = '无脾气虚'
        temp_data['spleenPredictType'] = spleenPredictType[idSet.index(data[0])]
        if data[13] == '1':
            temp_data['kidney_qi_deficiency'] = '有肾气虚'
        elif data[13] == '0':
            temp_data['kidney_qi_deficiency'] = '无肾气虚'
        temp_data['kidneyPredictType'] = kidneyPredictType[idSet.index(data[0])]
        result_data.append(temp_data)
    json_data['code'] = str(0)
    json_data['msg'] = ''
    json_data['total'] = len(result_data)
    offset = (int(page) - 1) * int(limit)  # 起始行
    endset = offset + int(limit)
    if endset > len(result_data):
        endset = len(result_data)

    cursor.close()
    conn.close()

    json_data['data'] = result_data[offset:endset]
    json_data = json.dumps(json_data)
    return json_data

#脉象预测服务
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
        filename_out = './files/pulseFileUTF.csv'

        # 输入文件的编码类型
        encode_in = 'utf-16 le'
        #输入表维度大小
        rows=2560
        cols=57
        formData['fileRead'] = 'success'
        try:
            data = pd.read_csv(filename_in, encoding=encode_in, header=None, nrows=rows,usecols=[i for i in range(cols)])
            data.to_csv(filename_out,encoding='utf-8',index=False, header=None)
            #转为numpy类型
            data_np=data.values
            # 调用模型计算脉搏类型预测结果
            result = predict.pulsePrediction(data_np)
            formData['pulseType'] = result
            formData['fileName'] = ''
            formData['channel0'] = data_np[:, 0].tolist()
            formData['channel1'] = data_np[:, 1].tolist()
            formData['channel2'] = data_np[:, 2].tolist()
            formData['channel3'] = data_np[:, 3].tolist()
            formData['channel4'] = data_np[:, 4].tolist()
            return json.dumps(formData)  # json.dumps封装
        except UnicodeDecodeError as e:
            data = pd.read_csv(filename_in, encoding='utf-8', header=None, nrows=rows,usecols=[i for i in range(cols)])
            data.to_csv(filename_out, encoding='utf-8', index=False, header=None)
            # 转为numpy类型
            data_np = data.values
            # 调用模型计算脉搏类型预测结果
            result = predict.pulsePrediction(data_np)
            formData['pulseType'] = result
            formData['fileName'] = ''
            formData['channel0'] = data_np[:, 0].tolist()
            formData['channel1'] = data_np[:, 1].tolist()
            formData['channel2'] = data_np[:, 2].tolist()
            formData['channel3'] = data_np[:, 3].tolist()
            formData['channel4'] = data_np[:, 4].tolist()
            return json.dumps(formData)  # json.dumps封装
        except ValueError as e:
            data = pd.read_csv(filename_in, encoding='utf-8', header=None, nrows=rows,usecols=[i for i in range(cols)])
            data.to_csv(filename_out, encoding='utf-8', index=False, header=None)
            # 转为numpy类型
            data_np = data.values
            # 调用模型计算脉搏类型预测结果
            result = predict.pulsePrediction(data_np)
            formData['pulseType'] = result
            formData['fileName'] = ''
            formData['channel0'] = data_np[:, 0].tolist()
            formData['channel1'] = data_np[:, 1].tolist()
            formData['channel2'] = data_np[:, 2].tolist()
            formData['channel3'] = data_np[:, 3].tolist()
            formData['channel4'] = data_np[:, 4].tolist()
            return json.dumps(formData)  # json.dumps封装
        except Exception as e:
            formData['fileRead'] = 'fail'
        else:
            formData['fileRead'] = 'fail'
        newData = json.dumps(formData)  # json.dumps封装
        return newData

#脉波展示，通道选择服务
@app.route('/post_ChannelNum', methods=["POST"])
def post_ChannelNum():
    formData={}
    # 获取前端请求的数据
    selectTestNum = request.form.get('selectChannelNum')
    testNum=int(selectTestNum)

    filename_in = './files/pulseFileUTF.csv'
    # 输入表维度大小
    rows = 2560
    cols = 57
    if(testNum==0):
        data = pd.read_csv(filename_in, encoding='utf-8', header=None, nrows=rows, usecols=[i for i in range(cols)])
        # 转为numpy类型
        data_np = data.values
        #填入前5个通道的序列数据，用于脉波展示
        formData['channel0'] = data_np[:, 0].tolist()
        formData['channel1'] = data_np[:, 1].tolist()
        formData['channel2'] = data_np[:, 2].tolist()
        formData['channel3'] = data_np[:, 3].tolist()
        formData['channel4'] = data_np[:, 4].tolist()
        return json.dumps(formData)  # json.dumps封装
    else:
        data = pd.read_csv(filename_in, encoding='utf-8', header=None, nrows=rows, usecols=[i for i in range(cols)])
        # 转为numpy类型
        data_np = data.values
        # 填入第testNum个通道的序列数据，用于脉波展示
        formData['channel'] = data_np[:, testNum-1].tolist()
        return json.dumps(formData)  # json.dumps封装

#脉象准确率验证服务
@app.route('/pulsePrediction_accuracy', methods=["POST"])
def pulsePrediction_accuracy():
    # 获取前端请求的数据
    selectTestNum = request.form.get('selectTestNum')
    testNum=int(selectTestNum)
    totalNum=875

    conn = POOL.connection(shareable=False)
    cursor1 = conn.cursor()
    idSet,predicted,labels,correct,total,accuracy = predict.mulPulsePrediction(testNum,totalNum,cursor1)
    cursor1.close()
    conn.close()
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

#脉象舌象综合验证服务
@app.route('/pulse_tongue_Prediction', methods=["POST"])
def pulse_tongue_Prediction():
    # 获取前端请求的数据
    selectTestNum = request.form.get('selectTestNum')
    testNum=int(selectTestNum)
    totalNum=198#有舌像又有脉象的数据量
    # 调用模型验证测试结果(读取文件速度太慢，直接写死用读好的数据)
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    idSet,properColorSet,mossColorSet,predicted,labels,correct,total,accuracy,tongue_results = predict.mulPulsePrediction2(testNum,totalNum,cursor)
    # 方案一：沉细-0 细-1 弦-2 弦细-3 滑-4 濡-5
    pulseType = ['沉细', '细', '弦', '弦细', '滑', '濡']
    predictType=[]
    labelType=[]
    for index in range(testNum):
        predictType.append(pulseType[predicted[index]])
        labelType.append(pulseType[labels[index]])
    formData = {}
    formData['testNum']=str(testNum)
    #脉象统计正确/错误预测数目
    formData['num_pos']=correct
    formData['num_neg']=total-correct
    formData['accuracy']=accuracy
    formData['predictType']=predictType
    formData['labelType']=labelType
    formData['idSet']=idSet
    #舌色、苔色列对应的标签信息
    formData['properColorSet'] = properColorSet
    formData['mossColorSet'] = mossColorSet
    # 舌象统计正确/错误预测数目，以及预测准确率《《待修改》》
    formData['tongue_accuracy'] = (tongue_results['tongue_color_accuracy'] + tongue_results['moss_color_accuracy']) / 2
    formData['tongue_num_pos'] = int(total * formData['tongue_accuracy'])
    formData['tongue_num_neg'] = total - formData['tongue_num_pos']
    # 舌象预测类型《《待修改》》
    formData['properColorPredictType'] = tongue_results['pred_tongue_colors']
    formData['mossColorPredictType'] = tongue_results['pred_moss_colors']

    tongueData = []
    for i in range(testNum):
        patient_id = tongue_results['sample_ids'][i]

        sql = ""
        if patient_id[0] == 'k':
            sql = "select * from dwd_kidney_info where id = '" + patient_id + "';"
        elif patient_id[0] == 'l':
            sql = "select * from dwd_lung_info where id = '" + patient_id + "';"
        else:
            sql = "select * from dwd_liver_info where id = '" + patient_id + "';"
        # 从数据库获取病人信息表
        patient_info = {}
        try:
            cursor.execute(sql)
            query_result = cursor.fetchall()
            col_names = pd.DataFrame(list(cursor.description)).iloc[:, 0].tolist()
            if len(query_result) != 0:
                for j in range(len(col_names)):
                    patient_info[col_names[j]] = str(query_result[0][j])
        except:
            print(patient_id + '病人信息获取失败！')

        img_stream = tongue_color_predict.img_stream(tongue_results['sample_img_paths'][i])
        pred = {
            "encode": img_stream,
            "true_ton_color": tongue_results['true_tongue_colors'][i],
            "pre_ton_color": tongue_results['pred_tongue_colors'][i],
            "true_coating_color": tongue_results['true_moss_colors'][i],
            "pre_coating_color": tongue_results['pred_moss_colors'][i],
            "patient_info": patient_info
        }
        tongueData.append(pred)

    cursor.close()
    conn.close()

    formData['tongueData'] = tongueData
    newData = json.dumps(formData)  # json.dumps封装
    return newData

#获取预测序列的用户信息（查三科表，脉象舌象综合）
@app.route('/patient_info_of_pulse_tongue_by_id', methods=['POST'])
def patient_info_of_pulse_tongue_by_id():
    page = request.form.get('page')  # 页数
    limit = request.form.get('limit')  # 每页显示的数量
    if page is None:
        page = 1
    if limit is None:
        limit = 1
    # 获取前端请求的数据
    idSet = json.loads(request.form.get('idSet'))
    predictType = json.loads(request.form.get('predictType'))
    labelType = json.loads(request.form.get('labelType'))
    properColorPredictType = json.loads(request.form.get('properColorPredictType'))
    mossColorPredictType = json.loads(request.form.get('mossColorPredictType'))
    properColorSet = json.loads(request.form.get('properColorSet'))
    mossColorSet = json.loads(request.form.get('mossColorSet'))
    json_data = {}
    result_data = []
    # 填充返回前端table的json数据（肾科）
    idStr="'"+",".join(idSet)+"'"
    sql = "select id,sex,age,tongue,pulse from dwd_kidney_info where FIND_IN_SET(id,"+idStr+") order by FIND_IN_SET(id,"+idStr+")"
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()

    # 填充返回前端table的json数据
    for data in totalQueryData:
        index = idSet.index(data[0])
        temp_data = {}
        temp_data['index'] = index
        temp_data['id'] = data[0]
        if data[1] == '1':
            temp_data['sex'] = '男'
        elif data[1] == '2':
            temp_data['sex'] = '女'
        temp_data['age'] = data[2]
        temp_data['tongue'] = data[3]
        # 舌质颜色 淡红（正常）0 淡白1 红2 暗/紫3
        if properColorSet[index] == '0':
            temp_data['properColor'] = '淡红'
        elif properColorSet[index] == '1':
            temp_data['properColor'] = '淡白'
        elif properColorSet[index] == '2':
            temp_data['properColor'] = '红'
        elif properColorSet[index] == '3':
            temp_data['properColor'] = '暗/紫'
        temp_data['properColorPredictType'] = properColorPredictType[index]
        # 苔色白（正常）0 黄1
        if mossColorSet[index] == '0':
            temp_data['mossColor'] = '白'
        elif mossColorSet[index] == '1':
            temp_data['mossColor'] = '黄'
        temp_data['mossColorPredictType'] = mossColorPredictType[index]
        temp_data['pulse'] = data[4]
        temp_data['labelType'] = labelType[index]
        temp_data['predictType'] = predictType[index]
        result_data.append(temp_data)

    # 填充返回前端table的json数据（肝科）
    sql = "select id,sex,age,tongue,pulse from dwd_liver_info where FIND_IN_SET(id," + idStr + ") order by FIND_IN_SET(id," + idStr + ")"
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()
    # 填充返回前端table的json数据
    for data in totalQueryData:
        index = idSet.index(data[0])
        temp_data = {}
        temp_data['index'] = index
        temp_data['id'] = data[0]
        if data[1] == '1':
            temp_data['sex'] = '女'
        elif data[1] == '2':
            temp_data['sex'] = '男'
        temp_data['age'] = data[2]
        temp_data['tongue'] = data[3]
        # 舌质颜色 淡红（正常）0 淡白1 红2 暗/紫3
        if properColorSet[index] == '0':
            temp_data['properColor'] = '淡红'
        elif properColorSet[index] == '1':
            temp_data['properColor'] = '淡白'
        elif properColorSet[index] == '2':
            temp_data['properColor'] = '红'
        elif properColorSet[index] == '3':
            temp_data['properColor'] = '暗/紫'
        temp_data['properColorPredictType'] = properColorPredictType[index]
        # 苔色白（正常）0 黄1
        if mossColorSet[index] == '0':
            temp_data['mossColor'] = '白'
        elif mossColorSet[index] == '1':
            temp_data['mossColor'] = '黄'
        temp_data['mossColorPredictType'] = mossColorPredictType[index]
        temp_data['pulse'] = data[4]
        temp_data['labelType'] = labelType[index]
        temp_data['predictType'] = predictType[index]
        result_data.append(temp_data)

    # 填充返回前端table的json数据（肺科）
    sql = "select id,sex,age,tongue,pulse from dwd_lung_info where FIND_IN_SET(id," + idStr + ") order by FIND_IN_SET(id," + idStr + ")"
    cursor.execute(sql)  # 获得所有符合条件的数据
    totalQueryData = cursor.fetchall()
    # 填充返回前端table的json数据
    for data in totalQueryData:
        index = idSet.index(data[0])
        temp_data = {}
        temp_data['index'] = index
        temp_data['id'] = data[0]
        if data[1] == '1':
            temp_data['sex'] = '女'
        elif data[1] == '2':
            temp_data['sex'] = '男'
        temp_data['age'] = data[2]
        temp_data['tongue'] = data[3]
        # 舌质颜色 淡红（正常）0 淡白1 红2 暗/紫3
        if properColorSet[index] == '0':
            temp_data['properColor'] = '淡红'
        elif properColorSet[index] == '1':
            temp_data['properColor'] = '淡白'
        elif properColorSet[index] == '2':
            temp_data['properColor'] = '红'
        elif properColorSet[index] == '3':
            temp_data['properColor'] = '暗/紫'
        temp_data['properColorPredictType'] = properColorPredictType[index]
        # 苔色白（正常）0 黄1
        if mossColorSet[index] == '0':
            temp_data['mossColor'] = '白'
        elif mossColorSet[index] == '1':
            temp_data['mossColor'] = '黄'
        temp_data['mossColorPredictType'] = mossColorPredictType[index]
        temp_data['pulse'] = data[4]
        temp_data['labelType'] = labelType[index]
        temp_data['predictType'] = predictType[index]
        result_data.append(temp_data)

    result_data.sort(key=lambda s: s["index"])#要根据原来的（折线）序号index进行排序
    json_data['code'] = str(0)
    json_data['msg'] = ''
    json_data['total'] = len(result_data)
    offset = (int(page) - 1) * int(limit)  # 起始行
    endset = offset + int(limit)
    if endset > len(result_data):
        endset = len(result_data)

    cursor.close()
    conn.close()

    json_data['data'] = result_data[offset:endset]
    json_data = json.dumps(json_data)
    return json_data

#肾象预测服务
@app.route('/kindney_prediction', methods=["POST"])
def kindney_prediction():
    # 获取前端请求的表单数据
    formData = request.form.to_dict()
    # 预测函数输入指标参数格式
    # dict1 = {'sex': '1', 'userage': '37', 'bloodCreatinine': '124.9', 'egfr': '73.953822', 'Tou': '舌红少苔', 'pulseType': '弦细'}
    # 转换前端参数为-》预测函数参数格式
    parm={}
    if(formData['sex']=='男'):
        parm['sex']=1
    elif(formData['sex']=='女'):
        parm['sex']=2
    parm['userage']=formData['userage']
    parm['bloodCreatinine']=formData['bloodCreatinine']
    parm['egfr']=formData['egfr']
    parm['Tou']=formData['tongueSymptoms']
    parm['pulseType']=formData['pulseSymptoms']
    try:
        # 调用模型计算脉搏类型预测结果
        result = kindney_symptom_predict.sigle_predict(parm)
        if(result[0]==1):
            formData['kindneyType']='肾阳虚'
        elif(result[0]==2):
            formData['kindneyType']='肾阴虚'
        formData['execute'] = 'success'
        return json.dumps(formData)  # json.dumps封装
    except Exception as e:
        formData['execute'] = 'fail'
    else:
        formData['execute'] = 'fail'
    newData = json.dumps(formData)  # json.dumps封装
    return newData

#肾象准确率验证服务
@app.route('/kindneyPrediction_accuracy', methods=["POST"])
def kindneyPrediction_accuracy():
    # 获取前端请求的数据
    selectTestNum = request.form.get('selectTestNum')
    testNum=int(selectTestNum)
    # 调用模型验证测试结果(读取文件速度太慢，直接写死用读好的数据)
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    idSet,predictType,labelType,correct,total,accuracy = kindney_symptom_predict.multi_predict(testNum,cursor)
    cursor.close()
    conn.close()
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

#肝象预测服务
@app.route('/liver_prediction', methods=["POST"])
def liver_prediction():
    # 获取前端请求的表单数据
    formData = request.form.to_dict()
    # 预测函数输入指标参数格式
    # dict1 = {'sex': '2', 'userage': '65', 'ALTD': '30', 'Tou': '舌苔黄腻', 'pulseType': '弦数'}
    # 转换前端参数为-》预测函数参数格式
    parm={}
    if(formData['sex']=='男'):
        parm['sex']=2
    elif(formData['sex']=='女'):
        parm['sex']=1
    parm['userage']=formData['userage']
    parm['ALTD']=formData['alt']
    parm['Tou']=formData['tongueSymptoms']
    parm['pulseType']=formData['pulseSymptoms']
    try:
        # 调用模型计算脉搏类型预测结果
        result = liver_symptom_predict.sigle_predict(parm)
        if(result[0]==1):
            formData['liverType']='肝胆湿热症'
        elif(result[0]==2):
            formData['liverType']='肝郁脾虚症'
        formData['execute'] = 'success'
        return json.dumps(formData)  # json.dumps封装
    except Exception as e:
        formData['execute'] = 'fail'
    else:
        formData['execute'] = 'fail'
    newData = json.dumps(formData)  # json.dumps封装
    return newData

#肝象准确率验证服务
@app.route('/liverPrediction_accuracy', methods=["POST"])
def liverPrediction_accuracy():
    # 获取前端请求的数据
    selectTestNum = request.form.get('selectTestNum')
    testNum=int(selectTestNum)
    # 调用模型验证测试结果(读取文件速度太慢，直接写死用读好的数据)
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    idSet,predictType,labelType,correct,total,accuracy = liver_symptom_predict.multi_predict(testNum,cursor)
    cursor.close()
    conn.close()
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

#肺象预测服务
@app.route('/lung_prediction', methods=["POST"])
def lung_prediction():
    # 获取前端请求的表单数据
    formData = request.form.to_dict()
    # 预测函数输入指标参数格式
    # dict1 = {'sex': '1', 'userage': '75', 'FEV1': '2.2','FVC':'2.71','FEV1%':'83.33','FEV1/FVC':'0.811808118','PEF':'4.02','Tou': '苔黄', 'pulseType': '脉弦滑'}
    # 转换前端参数为-》预测函数参数格式
    parm={}
    if(formData['sex']=='男'):
        parm['sex']=1
    elif(formData['sex']=='女'):
        parm['sex']=2
    parm['userage']=formData['userage']
    parm['wm_diagnosis']=formData['wm_diagnosis']
    parm['FEV1']=formData['FEV1']
    parm['FVC'] = formData['FVC']
    parm['FEV1%'] = formData['FEV1%']
    parm['FEV1/FVC'] = formData['FEV1/FVC']
    parm['PEF'] = formData['PEF']
    parm['Tou']=formData['tongueSymptoms']
    parm['pulseType']=formData['pulseSymptoms']
    try:
        formData['lungType'] = ''
        # 调用模型计算脉搏类型预测结果
        result = lung_symptom_predict.sigle_predict(parm)
        if(result[0]==1):
            formData['lungType']='肝气虚'
        if(result[1]==1 and formData['lungType']==''):
            formData['lungType'] += '脾气虚'
        else:
            formData['lungType'] += '，脾气虚'
        if (result[2] == 1 and formData['lungType']==''):
            formData['lungType'] += '肾气虚'
        else:
            formData['lungType'] += '，肾气虚'
        formData['execute'] = 'success'
        return json.dumps(formData)  # json.dumps封装
    except Exception as e:
        formData['execute'] = 'fail'
    else:
        formData['execute'] = 'fail'
    newData = json.dumps(formData)  # json.dumps封装
    return newData

#肺象准确率验证服务
@app.route('/lungPrediction_accuracy', methods=["POST"])
def lungPrediction_accuracy():
    # 获取前端请求的数据
    selectTestNum = request.form.get('selectTestNum')
    testNum=int(selectTestNum)
    # 调用模型验证测试结果(读取文件速度太慢，直接写死用读好的数据)
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    idSet,predictType1,predictType2,predictType3,labelType1,labelType2,labelType3,correct1,correct2,correct3,total,accuracy1,accuracy2,accuracy3 = lung_symptom_predict.multi_predict(testNum,cursor)
    cursor.close()
    conn.close()
    formData = {}
    formData['testNum']=str(testNum)
    formData['num_pos1']=correct1
    formData['num_pos2'] = correct2
    formData['num_pos3'] = correct3
    formData['num_neg1']=total-correct1
    formData['num_neg2'] = total - correct2
    formData['num_neg3'] = total - correct3
    formData['accuracy1']=accuracy1
    formData['accuracy2'] = accuracy2
    formData['accuracy3'] = accuracy3
    formData['predictType1']=predictType1
    formData['predictType2'] = predictType2
    formData['predictType3'] = predictType3
    formData['labelType1']=labelType1
    formData['labelType2'] = labelType2
    formData['labelType3'] = labelType3
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
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    cursor.execute(sql)  # 执行sql语句
    res = cursor.fetchall()  # 取数据
    cursor.close()
    conn.close()
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
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    cursor.execute(sql)  # 执行sql语句
    res = cursor.fetchall()  # 取数据
    cursor.close()
    conn.close()
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
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
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

    cursor.close()
    conn.close()

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
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
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
    cursor.close()
    conn.close()

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
    cur_path_raw='static/data/tongueimage/' + id + '.bmp'
    json_data = {}
    if(os.path.exists(cur_path_raw)):
        img_stream=return_img_stream(cur_path_raw)
        json_data['tongue_data'] = img_stream
    else:
        json_data['tongue_data'] = 'None'
    return json_data

@app.route('/tongue_pre',methods=['POST'])
def tongue_prediction():
    image_save_path = 'files'
    tongueImg = request.files["tongueImg"]
    tongueImg.save(os.path.join(image_save_path, 'input_img.bmp'))
    pred_tongue_color, pred_moss_color = tongue_color_predict.prediction(os.path.join(image_save_path, 'input_img.bmp'))

    predictResult = {
        "tongue_color": pred_tongue_color,
        "coated_tongue_color": pred_moss_color
    }
    predictResult = json.dumps(predictResult)
    return predictResult

@app.route('/tongue_batch_pre',methods=['POST'])
def tongue_batch_pre():
    num = int(request.form.get("num"))
    results = tongue_color_predict.batch_prediction(num)
    tongueData = []
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    for i in range(num):
        patient_id = results['sample_ids'][i]
        sql = ""
        if patient_id[0] == 'k':
            sql = "select * from dwd_kidney_info where id = '" + patient_id + "';"
        elif patient_id[0] == 'l':
            sql = "select * from dwd_lung_info where id = '" + patient_id + "';"
        else:
            sql = "select * from dwd_liver_info where id = '" + patient_id + "';"
        # 从数据库获取病人信息表
        patient_info = {}
        try:
            cursor.execute(sql)
            query_result = cursor.fetchall()
            col_names = pd.DataFrame(list(cursor.description)).iloc[:, 0].tolist()
            if len(query_result) != 0:
                for j in range(len(col_names)):
                    patient_info[col_names[j]] = str(query_result[0][j])
        except:
            print(patient_id + '病人信息获取失败！')

        img_stream = tongue_color_predict.img_stream(results['sample_img_paths'][i])
        pred = {
            "encode": img_stream,
            "true_ton_color": results['true_tongue_colors'][i],
            "pre_ton_color": results['pred_tongue_colors'][i],
            "true_coating_color": results['true_moss_colors'][i],
            "pre_coating_color": results['pred_moss_colors'][i],
            "patient_info": patient_info
        }
        tongueData.append(pred)

    cursor.close()
    conn.close()

    returnData = {"tongueData": tongueData, "tongue_color_accuracy": results['tongue_color_accuracy'],
                  "moss_color_accuracy": results['moss_color_accuracy']}

    returnData = json.dumps(returnData)
    return returnData

class DecimalEncoder(json.JSONEncoder):
    def default(self,o):
        if isinstance(o,decimal.Decimal):
            return float(o)
        super(DecimalEncoder,self).default(o)

@app.route('/sigle_patient_info',methods=['POST'])
def sigle_patient_info():
    id = request.form.get('id')  # 用户id
    if id[0] == 'k':
        type = 'kidney'
    elif id[0] == 'l':
        type = 'lung'
    else:
        type = 'liver'
    sql = "SELECT * FROM dwd_"+str(type)+"_info WHERE id='"+str(id)+"'"
    conn = POOL.connection(shareable=False)
    cursor = conn.cursor()
    cursor.execute(sql)
    column_name = cursor.fetchone()   # 获取数据
    cursor.close()
    conn.close()
    newData={}
    newData['data'] = column_name
    newData['type'] = type
    newData = json.dumps(newData, ensure_ascii=False,cls=DecimalEncoder)
    return newData

if __name__ == '__main__':
    app.run(debug=True)
