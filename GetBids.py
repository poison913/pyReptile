import os
import urllib
import urllib.request
import re
import threading
from urllib.error import URLError
from bs4 import BeautifulSoup
import pymssql
import time
import datetime
import uuid
import pyodbc

class QsSpider:
    def __init__(self):
        self.user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        self.header = {'User-Agent': self.user_agent}
        # 网址
        self.url = 'http://cg.hzft.gov.cn/www/noticelist.do?page.pageNum=%s'
        self.pagenum = 1
        self.iscontinue = 1
        self.lasttime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def start(self):
        self.getlasttime();
        self.load_html();
        timer = threading.Timer(60 * 60 * 24, self.start())
        timer.start()

    def load_html(self):
        # 获取网站的html页面
        try:
            web_path = self.url % str(self.pagenum)
            request = urllib.request.Request(web_path, headers=self.header)
            with urllib.request.urlopen(request) as f:
                html_content = f.read().decode('UTF-8')
                #print(html_content)
                self.pick_Info(html_content)
        except URLError as e:
            print(e.reason)
        return

    def pick_Info(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        tag_soup = soup.find(class_="c_list_item")
        print (tag_soup.contents)
        for index in range(len(tag_soup.contents)):
            if(index % 2) != 0:
                #print(tag_soup.contents[index])
                ts = tag_soup.contents[index]
                title = ts.contents[1].text.replace(ts.contents[1].text[0:9], '').replace('\\r', '\r').replace('\\n', '\n').replace('\\t', '\t').strip()
                url = "http://cg.hzft.gov.cn/"+ ts.contents[1]['href']
                publishtime = ts.contents[3].text
                if('采购结果公告' in  title):
                    continue
                if(self.time_cmp(self.lasttime,datetime.datetime.strptime(publishtime.strip(), "%Y-%m-%d"))):
                    self.iscontinue = 0
                    print('结束啦')
                    break;
                if('水利' in title or '信息化' in title or '软件' in title or '硬件' in title or '遥感' in title or '大数据' in title ):
                    self.insert(title,url,publishtime)
        if (self.iscontinue == 1):
            self.pagenum = self.pagenum + 1
            self.load_html();

    def getlasttime(self):
        conn = pymssql.connect(host='127.0.0.1',user= 'sa', password='123456', database='Project_Test' )
        #conn = pymssql.connect(host="db.dcxxsoft.xyz,14353", user="sa", password="wepUWX4mhgqFZKa5", database="internal_management_sys")
        #conn = pyodbc.connect('DRIVER={SQL Server};SERVER=db.dcxxsoft.xyz,14356;DATABASE=PubliceResource;UID=sa;PWD=BbZnC3YPtuAj1qzN')
        cursor = conn.cursor()

        cursor.execute('SELECT *  FROM [dbo].[Bidding]  where Source = %s order by PublicTime desc', '杭州市政府采购网')
        row = cursor.fetchone()
        while row:
            self.lasttime = row[6]
            if (row[6] == None):
                self.lasttime = datetime.date(datetime.date.today().year, 1, 1)
            break;

        # 关闭连接
        conn.close()

    def insert(self,title,url,publishtime):
        conn = pymssql.connect(host='127.0.0.1', user='sa', password='123456', database='Project_Test')
        cursor = conn.cursor()

        insert = " INSERT INTO Bidding (BiddingID,Title,Url,Source,PublicTime,CreateTime)values ('"+str(uuid.uuid1())+"','"+title+"','"+url+"','杭州市政府采购网','"+publishtime+"','"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) +"' ) "
        cursor.execute(insert)
        conn.commit()

        # 关闭连接
        conn.close()

    def  time_cmp(self,first_time, second_time):
        return first_time > second_time

def fun_timer( ):
    sjspider = QsSpider()
    sjspider.start()
    timer = threading.Timer(60*60*24, fun_timer)
    timer.start()

timer = threading.Timer(1,fun_timer)  #首次启动
timer.start()