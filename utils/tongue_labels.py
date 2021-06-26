import pandas as pd
import pymysql

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


def produce_tongue_labels():
    # 从数据库获取病人信息表
    try:
        cursor.execute("SELECT id,tongue FROM ods_kidney_info;")
    except:
        print('从服务器获取肾病舌形数据失败')
        return 0
    query_result_kidney = cursor.fetchall()
    col_names = pd.DataFrame(list(cursor.description)).iloc[:,0].tolist()
    tongue_kidney= pd.DataFrame(list(query_result_kidney), columns=col_names)

    try:
        cursor.execute("SELECT id,tongue FROM ods_liver_info;")
    except:
        print('从服务器获取肝病舌形数据失败')
        return 0
    query_result_liver = cursor.fetchall()
    col_names = pd.DataFrame(list(cursor.description)).iloc[:,0].tolist()
    tongue_liver= pd.DataFrame(list(query_result_liver), columns=col_names)
    try:
        cursor.execute("SELECT id,tongueA as tongue FROM ods_lung_info;")
    except:
        print('从服务器获取肺病舌形数据失败')
        return 0
    query_result_lung = cursor.fetchall()
    col_names = pd.DataFrame(list(cursor.description)).iloc[:,0].tolist()
    tongue_lung= pd.DataFrame(list(query_result_lung), columns=col_names)
    result_raw=[]
    for i in range(len(tongue_kidney)):
        result_raw.append([tongue_kidney.iloc[:,0][i],str(tongue_kidney.iloc[:,1][i])])
    for i in range(len(tongue_liver)):
        result_raw.append([tongue_liver.iloc[:,0][i],str(tongue_liver.iloc[:,1][i])])
    for i in range(len(tongue_lung)):
        result_raw.append([tongue_lung.iloc[:,0][i],str(tongue_lung.iloc[:,1][i])])
    result_raw=pd.DataFrame(result_raw)
    result_raw.columns=['id','tongue']
    result=tongue_code(result_raw)
    # result.to_excel('files/tongue_all_features.xls', index=False)
    result.to_csv('../files/tongue_all_features.csv', index=False)
    print(result)


def tongue_code(tongue):
    import re
    # 对舌的标签描述进行编码
    tongue['tongue_proper_color'] = 0  # 舌质颜色 淡红（正常）0 淡白1 红2 暗/紫3
    tongue['tongue_proper_shape_pang'] = 0  # 舌质形态 正常0 胖1  裂纹齿印(太少不用)
    tongue['tongue_proper_shape_neng'] = 0  # 舌质形态 正常0  嫩1
    tongue['tongue_proper_shape_chi'] = 0  # 舌质形态 正常0  有齿痕或齿印 1
    tongue['tongue_moss_color'] = 0  # 苔色白（正常）0 黄1
    tongue['tongue_moss_nature'] = 0  # 苔质 薄（正常）0  少1  腻2
    # 舌色编码
    patt0 = r'.*淡(?!红).*'
    tongue.loc[~tongue['tongue'].apply(lambda x: re.match(patt0, x)).isna(), 'tongue_proper_color'] = 1
    patt1 = r'.*[^淡]红.*'
    tongue.loc[~tongue['tongue'].apply(lambda x: re.match(patt1, x)).isna(), 'tongue_proper_color'] = 2
    tongue.loc[tongue['tongue'].str.contains('暗'), 'tongue_proper_color'] = 3
    tongue.loc[tongue['tongue'].str.contains('紫'), 'tongue_proper_color'] = 3
    # 舌形编码
    tongue.loc[tongue['tongue'].str.contains('胖'), 'tongue_proper_shape_pang'] = 1
    tongue.loc[tongue['tongue'].str.contains('嫩'), 'tongue_proper_shape_neng'] = 1
    tongue.loc[tongue['tongue'].str.contains('齿'), 'tongue_proper_shape_chi'] = 1
    # 苔色编码
    tongue.loc[tongue['tongue'].str.contains('黄'), 'tongue_moss_color'] = 1
    # 苔质编码
    tongue.loc[tongue['tongue'].str.contains('少'), 'tongue_moss_nature'] = 1
    tongue.loc[tongue['tongue'].str.contains('腻'), 'tongue_moss_nature'] = 2
    return tongue

if __name__ == '__main__':
    produce_tongue_labels()