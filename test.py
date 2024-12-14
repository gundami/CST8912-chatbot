
import pymssql

# 配置信息
server = 'cst8912-chatbot.database.windows.net'
database = 'user'
username = 'gundami'
password = 'Cyy@@52363465'

# 建立连接
try:
    connection = pymssql.connect(
        server=server, 
        user=username, 
        password=password, 
        database=database
    )
    print("成功连接到 Azure SQL Server!")

    # 创建游标对象
    cursor = connection.cursor()

    # 执行查询
    cursor.execute("SELECT TOP 5 * FROM your_table")
    for row in cursor.fetchall():
        print(row)

    # 关闭连接
    cursor.close()
    connection.close()
except Exception as e:
    print("连接失败:", e)
