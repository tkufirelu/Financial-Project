import mysql.connector

# 連線到 MariaDB
conn = mysql.connector.connect(
    host="localhost",
    user="firelu",
    password="atx121",
    database="finan",
    charset="utf8mb4",
    collation="utf8mb4_general_ci"
)

cursor = conn.cursor()

# 建立 cash 資料表
cursor.execute(
    """CREATE TABLE cash (
        transaction_id INT PRIMARY KEY AUTO_INCREMENT, 
        taiwanese_dollars INT, 
        us_dollars FLOAT, 
        note VARCHAR(30), 
        date_info DATE
    )"""
)

# 建立 stock 資料表
cursor.execute(
    """CREATE TABLE stock (
        transaction_id INT PRIMARY KEY AUTO_INCREMENT, 
        stock_id VARCHAR(10), 
        stock_num INT, 
        stock_price FLOAT, 
        processing_fee INT, 
        tax INT, 
        date_info DATE
    )"""
)

conn.commit()
conn.close()