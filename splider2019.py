#!/usr/bin/python
#coding:utf-8
import requests,re,os,time,urllib,urllib2,random
import json
import MySQLdb
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

"""
python2.7.x版本

"""

C = {"SITE":{},"DBCONFIG":{},"FIELD":{},"SAVEAPI":'',"Thread":1,"HEADER":{}}

#数据采集发布的API 功能未整合 预留
C['SAVEAPI'] = ''

#MYSQL数据库连接配置 采集数据存储
C['DBCONFIG']['save_host'] = '127.0.0.1'
C['DBCONFIG']['save_dbname'] = 'ceshi' #必须提前创建或存在数据库
C['DBCONFIG']['work_data'] = 'work_data' #指定数据保存表 自动创建 支持使用现有表
C['DBCONFIG']['work_log'] = 'work_log'  #指定日志保存表 自动创建
C['DBCONFIG']['save_user'] = 'root'
C['DBCONFIG']['save_password'] = '12345678'

"""
采集规则配置开始
"""
C['SITE']['home'] = 'http://www.51tietu.net'
C['SITE']['list_url'] = ['http://www.51tietu.net/weitu/','']#入口列表页 只要采集规则适用就支持多个
C['SITE']['is_json'] = False #暂用不到 就是采集接口的
C['SITE']['items_start'] = '<div class="list4 category">' #列表页范围切片开始
C['SITE']['items_end'] = '<div class="pager">' #列表页范围切片结束
C['SITE']['items_url'] = ' <li><h2><a target="_blank" href="(.+?)">(?:.+?)</a></h2></li>' #要提取的链接正则
C['SITE']['fiter_preg_before'] = ['style="[^"]+"','align="(.+?)"'] #正文提取前进行的正则过滤 正文提取只保留 p,img
C['SITE']['fiter_str_end'] = {"www.51tietu.net":"www.xxx.com","本文作者":"原文",'class="lazy"':''}#正文提取后进行的字符替换 比如目标网址替换 网站名称替换
C['SITE']['downpic'] = False #是否下载图片
C['SITE']['downpath'] = '/usr/tmp/test2019' #如果要下载图片 保存到指定目录请注意权限，如果运行脚本不是root用户时
C['SITE']['pichost'] = 'http://img.xxx.com/upload/' #图片下到本地了，如果上传到服务器上会在什么域名和目录，可预先设定了一并先存到数据库


#*****设置采集字段和采集规则 采集字段同时名称会是数据表的保存字段 如果使用现有表则应该对应现有表字段名*****

C['FIELD']['title'] = '<h1>(.+?)</h1>' #获取标题的正则
C['FIELD']['content'] = '<div class="pic-box">([\S\s]*?)</div>'
C['FIELD']['addtime'] = '[NOW]' #[NOW]是唯一一个保留标签，会在插入时替换成当前时间
C['USE_FILTER'] = 'content' #需要使用过滤的字段，必须是上面设置的，比如现在的 C['FIELD']['content']

#理论上以下不需要手工干预

if(C['SITE']['home'].find('https://') != -1):
	C['ISHTTPS'] = True
	C['HOST'] = C['SITE']['home'].replace("https://","")
else:
	C['ISHTTPS'] = False
	C['HOST'] = C['SITE']['home'].replace("http://", "")

C['HEADER'] = {"User-Agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
			   "Referer":C['HOST'],"Host":C['HOST'],"Accept-Language":"zh-CN,zh;q=0.8,zh-TW;q=0.6,ar;q=0.4,en;q=0.2","Accept-Encoding":"gzip, deflate","Connection":"keep-alive",
			   "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"}

"""
采集规则配置结束
"""



def httpget(test = False):
	print "开始采集..."
	print "检查表..."
	check_table()
	print "--------------------------"
	for url in C['SITE']['list_url']:
		print("正在获取"+url+"列表内容")
		if url != '':
			try:
				html = requests.get(url, headers=C['HEADER'])
				if html != None:
					url_list = get_item(html.content)
					for work_url in url_list:
						DB = get_db()
						cur = DB.cursor()
						if check_log(work_url) == 0:
							print("正在采集"+str(work_url)+"......")
							if(test == True):
								news = get_content(work_url)
								for field in C['FIELD']:
									print "------------------------------------------------"
									if field == C['USE_FILTER']: #正文内容需要下载图片到本地
										news[field] = check_img(news[field])
									print field+':'
									print news[field]
								print("http测试 运行结束")
								exit(0)
							else:
								#构造添加的SQL
								news = get_content(work_url)
								insert_sql = "insert into " + C['DBCONFIG']['work_data'] + "("
								for field in C['FIELD']:
									insert_sql += str(field)+","
								insert_sql = insert_sql[:-1] #移除最后一个都号
								insert_sql += ")values("
								for field in C['FIELD']:
									if field == C['USE_FILTER']: #正文内容需要下载图片到本地
										news[field] = check_img(news[field])
									insert_sql += "'"+str(news[field])+"',"
								insert_sql = insert_sql[:-1]  # 移除最后一个都号
								insert_sql += ")"
								cur.execute(insert_sql)
								DB.commit()
								print "------------------------------------------------"
								print "采集入库完成"
								#print insert_sql
								#添加到日志
								cur.execute("insert into "+C['DBCONFIG']['work_log']+" (url)values('%s')" % work_url)
								DB.commit()
								print work_url
						else:
							print(work_url+"已经采集过了")
						DB.close()
				else:
					print("列表url采集不到")
			except Exception as e:
				print(e)
	print("http 采集运行结束")

def get_db():
	return MySQLdb.connect(C['DBCONFIG']['save_host'], C['DBCONFIG']['save_user'], C['DBCONFIG']['save_password'],C['DBCONFIG']['save_dbname'],charset="utf8")

def http_post(url,data):
	header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',"Content-Type": "application/json"}
	req = urllib2.Request(url=url, data=data, headers=header_dict)
	res = urllib2.urlopen(req)
	res = res.read()
	return res

#检查或创建表
def check_table():
	DB = get_db()
	cur = DB.cursor()
	#日志表
	log_sql = "create table if not exists "+C['DBCONFIG']['work_log']+" (id int primary key auto_increment,url varchar(220) not null,index(url))default charset=utf8"
	cur.execute(log_sql)

	#数据表
	work_sql = "create table if not exists "+C['DBCONFIG']['work_data']+" (id int primary key auto_increment"
	for field in C['FIELD']:
		if field == C['USE_FILTER']:
			work_sql += ","+str(field)+" text not null"
		else:
			work_sql += "," + str(field) + " varchar(200) not null"
	work_sql += ")default charset=utf8"
	#print work_sql
	cur.execute(work_sql)
	DB.close()

#检查一url是否已经采集过
def check_log(url):
	DB = get_db()
	cur = DB.cursor()
	#检查一url是否已经存在
	cur.execute("select id from "+C['DBCONFIG']['work_log']+" where url ='%s'"%url)
	result = cur.fetchone()
	DB.close()
	if result != None:
		return 1
	else:
		return 0


#发布数据
def api_post(title,content):
	jdata = {}
	jdata['title'] = title
	jdata['content'] = content
	jdata_str = json.dumps(jdata)
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',"Content-Type": "application/json"}
	print http_post('http://www.xxxx.com/api_pnews',jdata_str)
	
#图片下载
def down_pic(url):
	file_path = C['SITE']['downpath']
	time_str = time.strftime("%Y-%m-%d",time.localtime())
	time_str2 = time.strftime("%Y%m%d%H%M%S",time.localtime())
	try:
		file_path = file_path+'/'+time_str
		if not os.path.exists(file_path):
			os.makedirs(file_path) #不使用os.makedir, os.makedirs功能同mkdir -p
		#图片扩展名
		file_suffix = os.path.splitext(url)[1]
		#新文件名
		file_name = time_str2+str(random.randint(0,999999))+file_suffix
		file_name = file_path +'/'+file_name
		urllib.urlretrieve(url,file_name)
		return file_name.replace(file_path,C['SITE']['pichost']+'/'+time_str)
	except Exception as e:
		print(e)
	return url

#网址补全
def check_http(url):
	if url.find("://") == -1:
		return  C['SITE']['home']+url
	else:
		return url

#检查内容中的图片，对其进行网站补全 或 下载
def check_img(content):
	img_rule = '<img(.+)src="([^ ]+)"'
	result = re.findall(img_rule,content)
	if result:
		for src in result:
			content = content.replace(src[1],down_pic(check_http(src[1])))
			time.sleep(1)
	return content

#提取需要采集的url列表
def get_item(content):
	result = False
	if C['SITE']['is_json'] != True:
		#第一次切片
		first_result = content.split(C['SITE']['items_start'])[1]
		#第二次切片
		second_result = first_result.split(C['SITE']['items_end'])[0]
		result = re.findall(C['SITE']['items_url'],second_result)
	else:
		result = re.findall(C['SITE']['items_url'],content)
	url = [] #定义一个结果List
	#print(result)
	if result:
		for str in result:
			if str != None:
				url.append(check_http(str)) #把网址添加到List中
		
		return url
	else:
		return 0

		

#提取内容页
#参数 要采集的子页url
def get_content(url):
	result = {} #定义结果
	html = requests.get(url, headers=C['HEADER'])
	for field in C['FIELD']:
		if C['FIELD'][field] == '[NOW]':
			result[field] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
		else:
			field_result = re.search(C['FIELD'][field],html.content)
			if field_result != None:
				result[field] = field_result.group(1)
				if field == C['USE_FILTER']:
					result[field] = strip_tags(result[field],['p','img'],C['SITE']['fiter_str_end'],C['SITE']['fiter_preg_before'])
			else:
				result[field] = ''
	return result


#过滤html标签，并可保留指定标签
#参数 内容,保留的标签如 ['p', 'img'],过滤的字符['小日本','印度阿三'],['附加过滤正则比如alt="xx"']
#返回过滤后的内容
def strip_tags(html,tags=None,strs=None,filter_ot=None):
	#过滤预设的正则内容
	for ot in filter_ot:
		html = re.compile(ot,re.S).sub('',html)
	#保留标签处理
	for tag in tags:
		html = html.replace('<'+tag,'{:tag'+tag)
		html = html.replace('</'+tag+'>','{:tag/'+tag+'}')
	#过滤所有多余<>标签
	dr = re.compile(r'<([^>]+)>',re.S)
	html = dr.sub('',html)
	#还原保留的
	for tag in tags:
		html = html.replace('{:tag'+tag,'<'+tag)
		html = html.replace('{:tag/'+tag+'}','</'+tag+'>')
	#过滤字符
	for str in strs:
		html = html.replace(str,'')
	return html	

"""
程序运行入口
"""
if len(sys.argv)>1:
	work_type = sys.argv[1]
	if work_type == 'httptest':
		httpget(True)
	if work_type == 'http':
		httpget(False)
else:
	print("hell world")

