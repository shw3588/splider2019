# splider2019  

## 简单实用的python爬虫脚本，支持下图，数据清洗过滤，自动建表字段并存储入库Mysql,支持API POST发布 
第一次传东西，没什么水平，见谅。
若有疑问，欢迎访问我的博客留言讨论，一起学习进步 https://www.isres.com/

## 应用场景：  
crontab 定时监控的抓取某个列表实时的更新，然后发布或保存  

## 基本依赖：
pip install --upgrade pip
yum install -y mysql-devel
pip install MySQL-python -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple/


## 目前功能点  
1.下载图片本地化  
2.数据MYSQL入库  
3.数据过滤清洗  
4.采集字段灵活定义 存储表根据爬中字段创建MYSQL字段，也可直接应用于生产环境的数据库，根据生产库设置爬虫字段  

通过计划任务每3分钟调用脚本以达到实时与采集目标站点同步更新的效果，图片可用同步软件与远程同步。  
暂不要每分钟，因为脚本执行时间的问题，可能会出现越来越多的进程。  


## 计划功能点  
1.多线程  
2.进程检查  
3.分页与历史数据的抓取（已有，还未整合进这版）  
4.采集数据接口提交 （已有，还未整合进这版）  


## 使用方法，理论上环境没问题了，预创建的数据库OK了，这脚本可直接运行测试了。  
python splider2019.py httptest 测试并显示采集的一条数据  
python splider2019.py http 正式采集  


## 配置方法  

参考代码中的注释即可  
```

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
C['DBCONFIG']['save_password'] = '123456'

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

```


## 效果图 动态图加载比较慢 耐心等下：  

*** 演示用的目标采集网址不稳定，时不时就connect timeout，录这个我都试了几次。 
*** 现在换其它的懒得重新写采集规则，虽然不花太多时间

*** 第一图展示的就是显示采集到的一条数据，常用于规则配置好后的验证和修改测试等。

*** 第二图展示的是一个空数据库，爬虫自动创建表 字段，并完成数据入库，在本机看到图片已经下载,字段根据 并记录日志和排重

![1](https://www.isres.com/usr/uploads/2019/07/1444257172.gif)  

*** 第二图展示的是一个空数据库，爬虫自动创建表 字段，并完成数据入库，在本机看到图片已经下载,字段根据 并记录日志和排重  
*** 开始采集之后会延迟几秒，换个目标网址采集就不会这么慢了。  
    
![2](https://www.isres.com/usr/uploads/2019/07/313360480.gif)  
