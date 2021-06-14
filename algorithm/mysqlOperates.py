
import pymysql
#连接数据库
def get_conn():
    try:
        conn = pymysql.connect(
            host='58.199.160.140',
            port=3306,
            user='root',
            passwd='000000',
            db='medical_dw',
            charset='utf8'
        )
        print('数据库连接成功！')
        return conn
    except:
        print('数据库连接失败！')
        exit(0)

#数据库查询数据
def select_data(conn,sql):
    # 使用cursor()方法获取操作游标
    cur = conn.cursor()
    try:
        #执行sql查询语句
        cur.execute(sql)
        #获取全部查询数据
        results = cur.fetchall()
        return results
    except Exception as e:
        raise e
    finally:
        cur.close()

#数据库增加数据
def insert_data(conn,sql):
    cur = conn.cursor()
    try:
        cur.execute(sql)
        # 提交
        conn.commit()
    except Exception as e:
        # 错误回滚
        conn.rollback()
    finally:
        cur.close()

#数据库更新数据
def updata_data(conn,sql,data):
    cur = conn.cursor()
    try:
        cur.execute(sql % data)
        # 提交
        conn.commit()
    except Exception as e:
        # 错误回滚
        conn.rollback()
    finally:
        cur.close()

#数据库删除数据
def delete_data(conn,sql,id):
    cur = conn.cursor()
    try:
        # 向sql语句传递参数
        cur.execute(sql % id)
        # 提交
        conn.commit()
    except Exception as e:
        # 错误回滚
        conn.rollback()
    finally:
        cur.close()

#关闭数据库连接
def close_conn(conn):
    try:
        conn.close()
    except:
        print("关闭失败！！！")
        exit(0)

if __name__ == '__main__':
    conn = get_conn()

    conn.close()