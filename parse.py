import requests
from sys import argv,exit
from html.parser import HTMLParser
from threading import Thread
import sqlite3
#Блок с глобальными переменными
URL_domain=() #будем хранить в виде ('google','ru')
URL=''
xml_filename="sitemap.xml"
sql_filename="sitemap.sql"

#Блок с вспомогательными функциями
def CreateSQLTable(filename):
	connection=sqlite3.connect(filename)
	connection.close()
	#Так создали файл БД. Теперь заполним таблицы:
	connection=sqlite3.connect(filename)
	cursor=connection.cursor()

	create_table_page='''
	create table page(
	id integer primary key,
	name text);'''
#	create_table_relation="
#	create table relation(
#	id integer,
#	id_suburl integer);"

	cursor.execute(create_table_page)
#	cursor.execute(create_table_relation)

	cursor.close()
	connection.close()

#Вычленить протокол или вернуть None
def getLinkProtocol(url):
	ret=''
	#Если нет точки в link'е, то точно не глобальная, но может быть локальной с точкой в имени
	#А это "влоб", если протокол есть
	if url[:len("https")]=="https":
		return "https"
	if url[:len("http")]=="http":
		return "http"
	#А это полная проверка
	if url.find(".")!=-1 and url.find(":")<url.find(".") and url.find(":")<url.find("/"):
		ret=url[:url.find(":")]
		return ret
	if ret=='':
		return None





#Вернуть домен полностью в list'е или вернуть None
def getLinkDomain(url):
	ret=''
	if url.find(".")==-1:
		return None
	protocol=getLinkProtocol(url)
	url+="/"
	if protocol in ('http','https'):
		if protocol=="http":
			ret=url[len("http://"):]

		if protocol=='https':
			ret=url[len("https://"):]
	elif protocol!=None:
		if url.find("/")<url.find("."):
			dot_pos=url.find(".")
			ret=url[:url.find("/",dot_pos)]
			if ret.find("/")!=-1:
				ret.replace("/","")
			ret=ret[ret.find(":")+1:]
			#return ret
		if url.find(":")<url.find("."):
			ret=url[url.find(":")+1]
				# ftp://ftpex.e-vo.ru
				# mail:main@mail.ri
				# file:///file.xml
				#брать от первой точки до слеша после точки подстроку и из нее, если в ней остался слеш (часть поторокола), то от слеша до конца
				#Если слеша не осталось, но есть :, то от : до конца
	else: #значит нет протокола, но возможен ":" так как указан порт, если есть домен. Или домена нет, если ссылка локальная
		if url.find(":")!=-1:
			ret=url[:url.find(":")]
		elif url.find("/")!=-1:
			ret=url[:url.find("/")]

	if ret=='':
		return None
	else:
		ret=ret[:ret.find("/")].split(".")
		#ret=(ret[-2],ret[-1])
		return ret




#Блок с объявлением рабочих классов

class PageParser(HTMLParser):
	"""Класс обрабатывающий html код страницы, вычленяющий ссылки и проверяющий их на валидность"""
	"""После создания экземпляра (без параметров)"""
	"""Вызывается функция feed(передается текст страницы)"""
	"""Затем вызывается функция getValid(передавая доменное имя сайта в виде tuple)"""
	"""Доменное имя передается в виде ("google","ru")"""
	result:list=[]
#	URL_domain:tuple=() #при создании экземпляра будем передавать домен URL'а. Значение будет равно глобальной переменной, заполняемой при запуске программы
	def handle_starttag(self,tag,attrs):
		isHaveHref=False
		href=''
		if tag!='link':
			for i in attrs:
				if i[0]=='href':
					isHaveHref=True
					href=i[1]
					break
			if isHaveHref:
				self.result.append(href)


	#getValid - это генератор по листу link'ов, возвращающий корректные ссылки
	def getValid(self,URL_domain:tuple):
		link=self.result
		#Блок переменных для уменьшения кол-ва расчетов в цикле
		js_string_len=len("javascript:") #это ключевое словов в ссылках, если ссылка запускает js код
		for i in link:
			isValid=False
			if i.find("#")==-1: #то есть ссылка не является пустой или ссылающейся на часть страницы 
				if i[:js_string_len]!='javascript:':
					#теперь проверим на потокол, если он есть
					#Если протокол есть и он не http или https - ссылка не валидна (Например, ссылка на почту mail:main@mail.ru)
					#Если протокол есть и он http или https - извлекаем домен и проверяем с стартовым доменом сайта
					#Домен не наш - ссылка не валидан. Если наш - возвращаем True
					#Если протокола нет - проверяем по домену
					#Если нет протокола и домена - возвращаем True
					link_protocol=getLinkProtocol(i)
					link_domain=getLinkDomain(i)
					if link_domain==None and link_protocol==None:
						yield URL.rstrip("/")+"/"+i.lstrip("/")
						continue
					if link_domain!=None and link_domain==URL_domain and link_protocol in ('http','https'):
						yield i
					if link_protocol!=None and link_protocol not in ('http','https'): # Например протокол mail:
						continue
					if link_protocol==None:
						if  link_domain==None:
							yield URL.rstrip("/")+"/"+i.lstrip("/")
						elif link_domain==URL_domain:
							yield i
						else:
							continue
				else:
					continue
			else:
				continue



# Класс для работы с БД и файловой системой(работа с sitemap.xml файлом)
# по которому мы создадим 1 экземпляр на программу, для экономии памяти и избежания deadlock'а при большом кол-ве потоков
class AnswerListener():
	"""Объект для работы с БД и файлом результатом (sitemap.xml и sitemap.sql)"""
	""" Создается 1 экземпляр класса для  экономии оперативной памяти"""
	""" SaveRecord(url) - проверка и запись ссылки в xml и sql""" 
	#"" ExistRecord(URL_page) - проверка на записали ссылку уже в xml ""
	# SaveToDB(URL_page) -  запись в БД в таблицу page""
	#" SaveRelation(URL,subURL) - запись связки URL и  subURL ссылкиm содержащейся в html коде страницы с адресом URL""
	def __init__(self,sql_filename,xml_filename):
		self.sql_filename=sql_filename
		self.xml_filename=xml_filename
		self.check_exist_sql_request=''' select count(*) from page where name="{}"'''
		self.insert_link_frompage=''' insert into page (name) values('{}')'''
	def ExistRecord(self,url):
		ExistInSql=False
		ExistInXML=False
		con=sqlite3.connect(sql_filename)
		cursor=con.cursor()
		check=cursor.execute(self.check_exist_sql_request.format(url))
		if check.fetchall()!=[(0,)]:
			ExistInSql=True
		check.close()
		con.close()

		#теперь проверим xml
		line=''
		location_url=''
		with open(self.xml_filename,"r") as f:
			line=f.readline()
			while line!='':
				line=line.strip()
				if line=="<url>" or line=="</url>":
					line=f.readline()
					continue
				elif line.find("<loc>")!=-1:
					location_url=line[ line.find(">")+1: line.find("</")]
					if location_url==url:
						ExistInXML=True
						break
					else:
						line=f.readline()
						continue
			else:
				ExistInXML=False
		if ExistInSql and ExistInXML:
			return True
		else:
			if ExistInSql:
				print("log:error url {} есть в базе, но нет в xml".format(url))
				return True
			elif ExistInXML:
				print("log:error url {} есть в xml, но нет в xml".format(url))
				return True
			else:
				return False

	def _SaveInXML(self,url):
		with open(self.xml_filename,"a") as f:
			f.write("<url>\n<loc>{}</loc>\n</url>\n".format(url))

	def _SaveInSQL(self,url):
		try:
			connect=sqlite3.connect(self.sql_filename)
			cursor=connect.cursor()
			cursor.execute(self.insert_link_frompage.format(url))
			connect.commit()
			cursor.close()
			connect.close()
		except:
			print("sql log: can't save url {} by req {}".format(url,self.insert_link_frompage.format(url)))

	def  SaveRecord(self,url):
		if not self.ExistRecord(url):
			self._SaveInSQL(url)
		self._SaveInXML(url)



# Worker для обработки ссылки
class ThreadWorker(Thread):
	def __init__(self,URL,thread_count=5): #thread_count - кол-во допускаемых под потоков
		Thread.__init__(self)
		self.URL=URL #ссылка по которой запускается worker
		global URL_domain
		self.site_domain=URL_domain #для операций сравнения принадлежности ссылкой к нашему сайту получаем глобальный tuple сайта
		self.Wait=False
	def run(self,AnswerWorker):
		print("log: thread URL {} start".format(self.URL))
		Parser=PageParser()
		Parser.feed(requests.get(self.URL).text)
		ValidLinkList=[]
		if len(Parser.result)!=0:
			self.Wait=True
			for i in Parser.getValid(self.site_domain):
				ValidLinkList.append(i)
			print("log: thread URL {} find {} link".format(self.URL,len(ValidLinkList)))
			for i in ValidLinkList:
				if not AnswerWorker.ExistRecord(i):
					AnswerWorker.SaveRecord(i)
					SubThread=ThreadWorker(i)
					SubThread.run(AnswerWorker)
					print("log: run subworker from {} url".format(i))
		print("log: thread URL {} end".format(self.URL))













if __name__=="__main__":
	if len(argv)==1:
		print("Укажите адрес для парсинга")
		exit()
	if len(argv)>2:
		print("Для работы нужен только адрес сайта")
		exit()
	URL=argv[1]
	try:
		req=requests.get(URL)
		if req.status_code!=200:
			print("Сайт не отвечает")
			exit()
	except:
		print("Не корректная ссылка")
		exit()

	xml_filename,sql_filename="sitemap.xml","sitemap.sql"
	#Раз прошлые проверки пройдены, то можем приступить к работе
	#Создадим файл sitemap.xml и sitemap.sql (sqlite3)
	with open(xml_filename,"w"):
		pass
	with open(sql_filename,"w"):
		pass



	#Что касаемо БД - заполним таблицы
	#Таблицы будут: page (id,name) - id link'а, name - адрес
	# Не реализовано в данной версии//relation (id_page,id_relation_page), id_page - будет отсылать к id таблицы page и указывать на ссылку для которой, мы указываем id ссылок полученных из html кода страницы
	# Не реализовано в данной версии//То есть relation - связывает страницы по их id из таблицы page
	# Не реализовано в данной версии//Благодаря связке можем построить иерархию сайта (например для html карты сайта)

	

	CreateSQLTable(sql_filename)
	
	#Создаем Worker
	#Каждый worker будет работать пока список, ещё не записанных ссылок, будет не пуст
	#Или список ссылок на странице, по которой запущен worker не пуст
	print("Запуск")
	AnswerWorkerObject=AnswerListener(sql_filename,xml_filename)
	AnswerWorkerObject.SaveRecord(URL)
	print("Подключились к БД")
	Worker=ThreadWorker(URL)
	print("Создали обработчик")
	Worker.run(AnswerWorkerObject)
	print("Запустили обработчик")
	print("Конец программы")
