from flask import Flask,render_template,request,g,redirect
import mysql.connector
import requests
import math
import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')

r=requests.get('https://tw.rter.info/capi.php')
currency=r.json()

app=Flask(__name__)


def get_db():
    if not hasattr(g,'_database'):
        g._database=mysql.connector.connect(
            host="localhost",
            user="firelu",
            password="atx121",
            database="finan",
            charset="utf8mb4",
            collation="utf8mb4_general_ci"
        )
        
    return g._database

@app.teardown_appcontext
def close_connection(exception):
    if hasattr(g,'_database'):
        g._database.close()     

@app.route('/')
def index():
    conn=get_db()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM cash")
    cash_result=cursor.fetchall()
    #計算台幣與美金總和
    taiwanese_dollars=0
    us_dollars=0
    for row in cash_result:
        taiwanese_dollars+=row[1]
        us_dollars+=row[2]
    #獲取匯率
    r=requests.get('https://tw.rter.info/capi.php')
    currency=r.json()
    total=math.floor(taiwanese_dollars+us_dollars*currency['USDTWD']['Exrate'])
    #取得所有股票資訊
    cursor.execute("SELECT * FROM stock")
    stock_result=cursor.fetchall()
    unique_stock_list=[]
    for data in stock_result:
        if data[1] not in unique_stock_list:
            unique_stock_list.append(data[1])
    #計算股票總市值
    total_stock_value=0
    
    #計算單一股票資訊
    stock_info=[]
    for stock in unique_stock_list:
        cursor.execute("SELECT * FROM stock WHERE stock_id=%s",(stock,))
        result=cursor.fetchall()
        stock_cost=0  #單一股票總花費
        shares=0  #單一股票股數
        for d in result:
            shares += d[2]
            stock_cost += d[2]*d[3]+d[4]+d[5]
        #取得目前股價
        url="https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&stockNo="+stock
        response=requests.get(url)
        data=response.json()
        price_array=data['data']
        current_price=float(price_array[len(price_array)-1][6])
        #單一股票總市值
        total_value=round(current_price*shares)
        total_stock_value += total_value
        #單一股票平均成本
        average_cost = round(stock_cost / shares ,2)
        #單一股票報酬率
        rate_of_return= round((total_value - stock_cost)*100 / stock_cost, 2)
        stock_info.append({'stock_id':stock,'stock_cost':stock_cost, 'total_value':total_value,'average_cost':average_cost, 'shares':shares, 'current_price':current_price, 'rate_of_return':rate_of_return})
        
        
    for stock in stock_info:
        stock['value_percentage'] = round(stock['total_value'] * 100 / total_stock_value, 2)
    
    #繪製股票圓餅圖
    if len(unique_stock_list) !=0:
        labels=tuple(unique_stock_list)
        sizes=[d['total_value'] for d in stock_info]
        fig, ax=plt.subplots(figsize=(6,5))
        ax.pie(sizes, labels=labels, autopct=None, shadow=None)
        fig.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        plt.savefig("static/piechart.jpg", dpi=200)
    else:
        try:
          os.remove("static/piechart.jpg")
        except:
            pass
        
    #繪製股票現金圓餅圖
    if us_dollars != 0 or taiwanese_dollars != 0 or total_stock_value != 0:
        labels=('USD','TWD','Stock')
        sizes=(us_dollars*currency['USDTWD']['Exrate'], taiwanese_dollars, total_stock_value)
        fig, ax=plt.subplots(figsize=(6,5))
        ax.pie(sizes, labels=labels, autopct=None, shadow=None)
        fig.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        plt.savefig("static/piechart2.jpg", dpi=200)
    else:
        try:
          os.remove("static/piechart2.jpg")
        except:
            pass
        
        
        
    data={'show_pic_1':os.path.exists('static/piechart.jpg') ,'show_pic_2':os.path.exists('static/piechart2.jpg'), 'total':total,'td':taiwanese_dollars,'ud':us_dollars,'currency':currency['USDTWD']['Exrate'],'cash_result':cash_result, 'stock_info':stock_info}
    return render_template('index.html',data=data)
    
@app.route('/cash')
def cash_form():
    return render_template('cash.html')

@app.route('/cash',methods=['POST'])
def submit_cash():
    #取得金額與日期資料
    taiwanese_dollars=0
    us_dollars=0
    if request.values['taiwanese-dollars'] != '':
        taiwanese_dollars=request.values['taiwanese-dollars']
    if request.values['us-dollars'] != '':
        us_dollars=request.values['us-dollars']
    note=request.values['note']
    date=request.values['date']
    
    #將資料寫入資料庫
    conn=get_db()
    cursor=conn.cursor()
    cursor.execute(
        "INSERT INTO cash (taiwanese_dollars,us_dollars,note,date_info) VALUES (%s, %s, %s, %s)",
        (taiwanese_dollars,us_dollars,note,date)
    )
    conn.commit()
       
    #將使用者導回主頁
    return redirect('/')

@app.route('/cash-delete',methods=['post'])
def cash_delete():
    transaction_id=request.values['id']
    conn=get_db()
    cursor=conn.cursor()
    cursor.execute("delete from cash where transaction_id=%s",(transaction_id,))
    conn.commit()
    return redirect('/')
    


@app.route('/stock')
def stock_form():
    return render_template('stock.html')

@app.route('/stock',methods=['post'])
def submit_stock():
    #取得股票資訊、日期資料
    stock_id=request.values['stock-id']
    stock_num=request.values['stock-num']
    stock_price=request.values['stock-price']
    processing_fee=0
    tax=0
    if request.values['processing-fee'] != '':
       processing_fee=request.values['processing-fee']
    if request.values['tax'] != '':
       tax=request.values['tax']   
    date=request.values['date']
    #更新資料庫資料
    conn=get_db()
    cursor=conn.cursor()
    cursor.execute("INSERT INTO stock (stock_id,stock_num,stock_price,processing_fee,tax,date_info) VALUES (%s,%s,%s,%s,%s,%s)",(stock_id,stock_num,stock_price,processing_fee,tax,date))
    conn.commit()   
    #將使用者導至首頁
    return redirect('/')
    


if __name__=='__main__':
    app.run(debug=True,port=80)