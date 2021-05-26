# Sitemap генератор на Python
## О проекте
Скрипт позволяет составить карту сайта в xml и sql виде. Спецификация для составления карты взята с ресурса https://www.sitemaps.org/ru/protocol.html

#### Кратко о формате хранения сайта карты
Для улучшения индексирования сайта поисковыми системами, разработчики сайтов составляют файл ``` sitemap.xml ``` в котором указывается информация о доступных страницах для просмотра.  
Карта сайта предоставляет поисковым системам только в xml формате. 

Пример описания формата - https://www.sitemaps.org/ru/protocol.html

Данный проект позволяет составлять sitemap на основе уже готового сайта.

#### Дополнительно реализовано сохранение результатов в sqlite3 базу

# Запуск скрипта
Для запуска требуется Python3.8+

Необходимость в дополнительных библиотеках отсутвует.

``` 
wget https://github.com/AVMineev/sitemap_generator/blob/main/parse.py
python3 parse.py "http://google.com"  
```
 
 В локальной директории создается sitemap.xml и sitemap.sql
 
 ### Результат работы
 
 **Важно**: индексирование поддоменов не производиться, так как не было указано необходимым в задании. То есть для ```google.com``` не будет записан ```edu.google.com``` в результат
 #### Хранение результата
 #####   sitemap.xml
  Запись производиться в виде
``` 
        ...
        <url>
        <loc>http://google.com</loc>
        </url>
        ...
```
#####    sitemap.sql
В базе создана таблица page Со структурой:
```
	create table page(
	id integer primary key,
	name text);
```
#### Отчет по работе проекта


#### Параметры компьютера на котором были получены результаты
   **CPU**: Intel Pentium (Intel BayTrail M Quad-Core 3530 2.58GHz)
   
   **OS**: Ubuntu 20.04.2 LTS
   
   **Memory**: 4GB
