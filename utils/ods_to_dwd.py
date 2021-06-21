# -*- coding:utf-8 -*-
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

# 使用cursor()方法创建一个游标对象cursor，用于执行SQL语句
cursor = db.cursor()

def ods_to_dwd_kidney():
    create_table_sql="CREATE TABLE `medical_dw`.`dwd_kidney_info` (" \
        "`id` varchar(10) CHARACTER SET 'utf8' NOT NULL COMMENT '编号'," \
        "`sex` char(1) COMMENT '性别（1=男 2=女）'," \
        " `age` INT NULL COMMENT '年龄'," \
        " `serum_creatinine` DECIMAL(10,1) COMMENT '血肌酐'," \
        "`eGFR` DECIMAL(15,8)," \
        "`symptoms_type` char(1) COMMENT '症型（1=肾阳虚 2=肾阴虚）'," \
        "`tongue` varchar(20) COMMENT '舌'," \
        "`pulse` varchar(20) COMMENT '脉'" \
        " ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"

    delete_data_sql="delete from dwd_kidney_info"


    insert_data_sql="insert into medical_dw.dwd_kidney_info(select lower(id),sex,age," \
                    "(case when serum_creatinine='正常' and sex=1 then floor(54+rand()*53) " \
                    "when serum_creatinine='正常' and sex=2 then floor(45+rand()*52) " \
                    "else serum_creatinine end) as serum_creatinine,IF(ISNULL(eGFR) " \
                    "OR eGFR='',-100,round(eGFR,8)) as eGFR,symptoms_type ,tongue,pulse " \
                    "from (select * from (select if(@id=a.id,@r:=@r+1,@r:=1) as rowNumber," \
                    "a.*,@id:=a.id from (select @id:=0,@r:=0) r, (select * from medical_dw.ods_kidney_info " \
                    "order by id) a ) as t where t.rowNumber =1) tt where serum_creatinine!='' " \
                    "and serum_creatinine!='无'and symptoms_type!='' and tongue!='' and pulse!='' " \
                    "and age!='' and sex!='')"


    update_eGFR_sql="update medical_dw.dwd_kidney_info set eGFR = " \
                    "case when sex = 1 and eGFR<1 " \
                    "then power(serum_creatinine/88.41,-1.154)*186*1.233*power(age,-0.203) " \
                    "when sex = 2 and eGFR<1 " \
                    "then power(serum_creatinine/88.41,-1.154)*186*1.233*power(age,-0.203)*0.742 " \
                    "else eGFR end"

    sql_list=[delete_data_sql,insert_data_sql,update_eGFR_sql]
    try:
        for sql in sql_list:
            cursor.execute(sql)
            db.commit()
    except:
        db.rollback()
    db.close()


def ods_to_dwd_lung():
    create_table_sql="CREATE TABLE `medical_dw`.`dwd_lung_info` (" \
                     "`id` varchar(10) CHARACTER SET 'utf8' NOT NULL COMMENT '编号'," \
                     "`sex` char(1) COMMENT '性别（1=女 2=男）'," \
                     "`age` INT NULL COMMENT '年龄'," \
                     "`Wesmedicine_diagnosis` varchar(20) COMMENT '西医诊断'," \
                     "`Lung_qi_deficiency` char(1) COMMENT '肺气虚'," \
                     "`spleen_qi_deficiency` char(1) COMMENT '脾气虚'," \
                     "`kidney_qi_deficiency` char(1) COMMENT '肾气虚'," \
                     " `FEV1` DECIMAL(10,2)," \
                     "`FVC` DECIMAL(10,2)," \
                     " `FEV1%` DECIMAL(10,2)," \
                     "`FEV1/FVC` varchar(20) COMMENT 'EV1/FVC改'," \
                     "`PEF` varchar(10)," \
                     "`tongue` varchar(20) COMMENT '舌'," \
                     "`pulse` varchar(20) COMMENT '脉'" \
                     ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"
    delete_data_sql = "delete from dwd_lung_info"

    insert_data_sql="insert into medical_dw.dwd_lung_info(" \
                    "select lower(id),sex,age,wm_diagnosis,lung_qi_deficiency,spleen_qi_deficiency," \
                    "kidney_qi_deficiency,`FEV1`,`FVC`,`FEV1%`,`FEV1/FVC`,`PEF`, tongueA," \
                    "pulseA from (select * from (select if(@id=a.id,@r:=@r+1,@r:=1) as rowNumber," \
                    "a.*,@id:=a.id from (select @id:=0,@r:=0) r, (select * from medical_dw.ods_lung_info " \
                    "order by id) a ) as t where t.rowNumber =1) tt " \
                    "where `FEV1` is not null " \
                    "and `FVC`is not null and `FEV1%` is not null and `FEV1/FVC` " \
                    "is not null and tongueA is not null and pulseA is not null)"

    sql_list=[delete_data_sql,insert_data_sql]
    try:
        for sql in sql_list:
            cursor.execute(sql)
            db.commit()
    except:
        db.rollback()
    db.close()



def ods_to_dwd_liver():
    create_table_sql="CREATE TABLE `medical_dw`.`dwd_liver_info` (" \
                     "`id` varchar(20) CHARACTER SET 'utf8' NOT NULL COMMENT '编号'," \
                     " `sex` char(1) COMMENT '性别（1=女 2=男）'," \
                     " `age` INT NULL COMMENT '年龄'," \
                     "  `ALT` DECIMAL(10,2) COMMENT 'ALT'," \
                     " `symptoms_type` char(1) COMMENT '症型（1=肝胆湿热症 2=肝郁脾虚症）'," \
                     " `tongue` varchar(20) COMMENT '舌'," \
                     " `pulse` varchar(20) COMMENT '脉'" \
                     " ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci"

    delete_data_sql = "delete from dwd_liver_info"

    insert_data_sql="insert into medical_dw.dwd_liver_info(" \
                    "select id,sex,age,ALT,symptoms_type,tongue,pulse from " \
                    "(select * from (select if(@id=a.id,@r:=@r+1,@r:=1) " \
                    "as rowNumber,a.*,@id:=a.id from (select @id:=null,@r:=0) r, " \
                    "(select * from medical_dw.ods_liver_info order by id) a ) " \
                    "as t where t.rowNumber =1) tt " \
                    "where age!='' and symptoms_type is not null " \
                    "and tongue!='' and pulse is not null and sex!='' and ALT is not null);"

    sql_list=[delete_data_sql,insert_data_sql]
    try:
        for sql in sql_list:
            cursor.execute(sql)
            db.commit()
    except:
        db.rollback()
    db.close()


