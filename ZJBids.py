import os
import urllib
import urllib.request
import pymssql
import time
import datetime
import uuid
import json
import threading

class ZJSpider:
    def __init__(self):
        self.user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        self.header = {'User-Agent': self.user_agent}
        # 网址
        self.url = 'http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults?pageSize=15&pageNo=%s&noticeType=10&url=http://notice.zcy.gov.cn/new/noticeSearch'
        self.pagenum = 1
        self.iscontinue = 1
        self.lasttime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def start(self):
        self.getlasttime();
        self.load_html();

    def load_html(self):
        # 获取网站的html页面
        try:
            web_path = self.url % str(self.pagenum)
            request = urllib.request.Request(web_path, headers=self.header)
            with urllib.request.urlopen(request) as f:
                html_content = f.read().decode('UTF-8')
                #print(html_content)
                j = json.loads(html_content)
                self.pick_Info(j)
        except BaseException as e:
            print(e.reason)
        return

    def pick_Info(self, html_content):
        for index in range(len(html_content["articles"])):
            ts = html_content["articles"][index]
            title = ts["title"]
            url = ts["url"]
            area = ts["districtName"]
            category = ts["mainBidMenuName"]
            try:
                timetip = int(ts["pubDate"][:-3])
                time_local = time.localtime(timetip)
                # dateArray = datetime.datetime.utctimetuple(int(ts["pubDate"][:-3]))
                publishtime = time.strftime("%Y-%m-%d", time_local)
                publishtime = datetime.datetime.strptime(publishtime.strip(), "%Y-%m-%d")
            except BaseException as e:
                print(e.reason)
                continue


            if (self.time_cmp(self.lasttime, publishtime)):
                self.iscontinue = 0
                print('结束啦')
                break;
            if ('水利' in title or '信息化' in title or '软件' in title or '硬件' in title or '遥感' in title or '大数据' in title):
                self.insert(title, url, publishtime,area,category)
        if (self.iscontinue == 1):
            self.pagenum = self.pagenum + 1
            self.load_html();

    def getlasttime (self):
        conn = pymssql.connect(host='127.0.0.1',user= 'sa', password='123456', database='Project_Test' )
        cursor = conn.cursor()

        cursor.execute('SELECT *  FROM [dbo].[Bidding]  where Source = %s order by PublicTime desc', '浙江政府采购')
        row = cursor.fetchone()
        while row:
            self.lasttime = row[6]
            if(row[6] == None ):
                self.lasttime = datetime.datetime(datetime.date.today().year,4,1)
            break;

        # 关闭连接
        conn.close()

    def insert(self, title, url, publishtime, area, category):
        conn = pymssql.connect(host='127.0.0.1', user='sa', password='123456', database='Project_Test')
        cursor = conn.cursor()

        insert = " INSERT INTO Bidding (BiddingID,Title,Url,Source,Area,Category,PublicTime,CreateTime)values ('"+str(uuid.uuid1())+"','"+title+"','"+url+"','浙江政府采购','"+area+"','"+category+"','"+publishtime.strftime("%Y-%m-%d")+"','"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) +"' ) "
        cursor.execute(insert)
        conn.commit()

        # 关闭连接
        conn.close()

    def  time_cmp(self,first_time, second_time):
        return first_time > second_time

def fun_timer( ):
    sjspider = ZJSpider()
    sjspider.start()
    timer = threading.Timer(60 * 60 * 24, fun_timer)
    timer.start()

timer = threading.Timer(1,fun_timer)  #首次启动
timer.start()