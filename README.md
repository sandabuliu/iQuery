# iQuey

数据仓库通用查询服务

## 最近更新
* 添加维度计算
* 支持窗口函数

## 安装依赖
```shell
pip install -r requirements.txt
```

根据所需要连接的数据仓库, 安装对应的扩展库
```shell
pip install sqlalchemy-hana      # hana
pip install ibm_db_sa            # db2
pip install PyHive               # hive
pip install impyla               # impala
pip install sqlalchemy-redshift  # redshift
pip install sqlalchemy-sqlany    # driver for SAP Sybase SQL Anywhere, developed by SAP
...
```

根据所需要连接的数据仓库, 安装对应的连接驱动
```shell
pip install MySQL-python       # mysql
pip install cx_Oracle          # oracle
pip install pymssql            # mssql
pip install psycopg2           # postgresql
pip install PyHive             # hive
pip install impyla             # impala
pip install pypyodbc           # odbc
pip install pyhdb              # hana
...
```

## 配置文件

```
[config]
log_cfg='conf/logging.conf'     # 日志配置文件
log_dir='./logs'                # 日志路径文件夹
port=8000                       # 服务默认端口
pool_size=50                    # 线程池数目
```

## 启动服务

```shell
python main.py
```

启动参数
```
main.py options:

  --debug                          debug模式 (default: False)
  --port                           服务端口
  --processors                     进程数 (default: 1)
```

## API 接口文档

### 计算接口

#### `GET` `/api/calculate/result` 获取计算结果

|参数名|类型|含义|参数位置|是否必选|示例|
|----|----|----|----|----|----|
|type|str|数据库类型|URL|√||
|host|str|数据库地址|URL|√||
|port|int|数据库端口|URL|||
|username|str|数据库用户名|URL|||
|password|str|数据库密码|URL|||
|alias|str|数据库其他连接参数|URL|||
|schema|str|数据库名称|URL|√||
|kwargs|str - `json`|数据库其他配置参数|URL|||
|xAxis|`str`/`json`|维度|BODY||`name`<br>`["name", "age"]`<br>`[{"params": ["cdatetime"], "func": "cast_year"}]`|
|yAxis|`str`/`json`|维度|BODY|√|`name`<br>`[{"name": "name", "func": "count"]`<br>`{"name": "name", "func": "count", "calculate": "percert"`|
|table|`str`/`json`|表名|BODY|√|`table_name`<br>`{"table": "test", "schema": "schema"}`|
|where|`str`/`json`|过滤条件|BODY||`age<2`|
|order|str - `json(list)`|排序|BODY||`[0]`<br>`[(0, "DESC"), 1]`|

`yAxis`中`calculate`对应取值：

`percent`: 百分比    
`accumulate`: 累加计算    
`same`: 同比    
`annular`: 环比  

##### 请求示例

```shell
curl -i -X POST 'http://127.0.0.1:8000/api/calculate/result?schema=bin_test&type=mysql&host=192.168.1.1&username=root&password=123456' -d '{"table": "faker91", "yAxis": [{"name": "name", "func": "count", "calculate": "same", "result_type": "rate"}], "xAxis": [{"params": ["cdatetime"], "func": "cast_year"}]}'
```
结果返回：

```json
{"data": [[0, null], [1970, null], [2009, -5], [2010, 4], [2011, 0], [2012, -6], [2013, 0], [2014, 3], [2015, 1], [2016, -1], [2017, 0], [2018, -4], [2019, 3], [2020, 1]], "columns": [{"type": "long", "name": "x_0"}, {"type": "long", "name": "anon_1"}]}
```  



### 数据库接口

#### `GET` `/api/schemas` 获取全部SCHEMA

|参数名|类型|含义|参数位置|是否必选|
|----|----|----|----|----|
|type|str|数据库类型|URL|√|
|host|str|数据库地址|URL|√|
|port|int|数据库端口|URL||
|username|str|数据库用户名|URL||
|password|str|数据库密码|URL||
|alias|str|数据库其他连接参数|URL||
|kwargs|str - `json`|数据库其他配置参数|URL||

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/api/db/schema?type=mysql&host=127.0.0.1&port=3306&username=root&password=123456'
```
结果返回：

```json
{"databases": ["information_schema", "mysql", "performance_schema"]}
```


#### `GET` `/api/tables` 获取数据库中全部表（含视图）

|参数名|类型|含义|参数位置|是否必选|
|----|----|----|----|----|
|type|str|数据库类型|URL|√|
|host|str|数据库地址|URL|√|
|port|int|数据库端口|URL||
|username|str|数据库用户名|URL||
|password|str|数据库密码|URL||
|alias|str|数据库其他连接参数|URL||
|schema|str|数据库名称|URL|√|
|kwargs|str - `json`|数据库其他配置参数|URL||

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/api/tables?type=mysql&host=127.0.0.1&port=3306&username=root&password=12345&schema=mysql'
```
结果返回：

```json
{"tables": [{"type": "table", "name": "columns_priv"}, {"type": "table", "name": "db"}, {"type": "table", "name": "event"}, {"type": "table", "name": "func"}, {"type": "table", "name": "general_log"}, {"type": "table", "name": "help_category"}, {"type": "table", "name": "help_keyword"}, {"type": "table", "name": "help_relation"}, {"type": "table", "name": "help_topic"}, {"type": "table", "name": "host"}, {"type": "table", "name": "ndb_binlog_index"}, {"type": "table", "name": "plugin"}, {"type": "table", "name": "proc"}, {"type": "table", "name": "procs_priv"}, {"type": "table", "name": "proxies_priv"}, {"type": "table", "name": "servers"}, {"type": "table", "name": "slow_log"}, {"type": "table", "name": "tables_priv"}, {"type": "table", "name": "time_zone"}, {"type": "table", "name": "time_zone_leap_second"}, {"type": "table", "name": "time_zone_name"}, {"type": "table", "name": "time_zone_transition"}, {"type": "table", "name": "time_zone_transition_type"}, {"type": "table", "name": "user"}]}
```


#### `GET` `/api/columns` 查看数据库表字段信息

|参数名|类型|含义|参数位置|是否必选|
|----|----|----|----|----|
|type|str|数据库类型|URL|√|
|host|str|数据库地址|URL|√|
|port|int|数据库端口|URL||
|username|str|数据库用户名|URL||
|password|str|数据库密码|URL||
|alias|str|数据库其他连接参数|URL||
|schema|str|数据库名称|URL|√|
|table|str|数据表名称|URL|√|
|kwargs|str - `json`|数据库其他配置参数|URL||

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/api/schema?type=mysql&host=127.0.0.1&port=3306&username=root&password=123456&schema=mysql&table=user'
```
结果返回：

```json
{"columns": [{"default": "''", "type": "str", "name": "Host", "nullable": false}, {"default": "''", "type": "str", "name": "User", "nullable": false}, {"default": "''", "type": "str", "name": "Password", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Select_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Insert_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Update_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Delete_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Drop_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Reload_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Shutdown_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Process_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "File_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Grant_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "References_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Index_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Alter_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Show_db_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Super_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_tmp_table_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Lock_tables_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Execute_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Repl_slave_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Repl_client_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_view_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Show_view_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_routine_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Alter_routine_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_user_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Event_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Trigger_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_tablespace_priv", "nullable": false}, {"default": "''", "type": "unicode", "name": "ssl_type", "nullable": false}, {"default": null, "type": "str", "name": "ssl_cipher", "nullable": false}, {"default": null, "type": "str", "name": "x509_issuer", "nullable": false}, {"default": null, "type": "str", "name": "x509_subject", "nullable": false}, {"default": "'0'", "autoincrement": false, "type": "int", "name": "max_questions", "nullable": false}, {"default": "'0'", "autoincrement": false, "type": "int", "name": "max_updates", "nullable": false}, {"default": "'0'", "autoincrement": false, "type": "int", "name": "max_connections", "nullable": false}, {"default": "'0'", "autoincrement": false, "type": "int", "name": "max_user_connections", "nullable": false}, {"default": "''", "type": "str", "name": "plugin", "nullable": true}, {"default": null, "type": "str", "name": "authentication_string", "nullable": true}]}
```

#### `GET` `/api/query/result` 获取查询结果

|参数名|类型|含义|参数位置|是否必选|
|----|----|----|----|----|
|type|str|数据库类型|URL|√|
|host|str|数据库地址|URL|√|
|port|int|数据库端口|URL||
|username|str|数据库用户名|URL||
|password|str|数据库密码|URL||
|alias|str|数据库其他连接参数|URL||
|schema|str|数据库名称|URL||
|sql|str|SQL 语句，标准SQL|URL|√|
|kwargs|str - `json`|数据库其他配置参数|URL||

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/api/query/result?type=mysql&host=127.0.0.1&port=3306&username=root&password=123456& schema=test&sql=select+*+from+test+limit+2'
```
结果返回：

```json
{
    "schema": [
        {"type": "number", "name": "id"},
        {"type": "string", "name": "name"},
        {"type": "string", "name": "addr"},
        {"type": "number", "name": "age"},
        {"type": "string", "name": "info"},
        {"type": "date",   "name": "birthday"}
    ],
    "data": [
        [5903367, "zhangsan", "beijing", 1, null, "1997-08-24 11:56:08"],
        [5903369, "lisi", "shanghai", 1, null, "1995-08-24 11:56:08"]
    ]
}
```

#### `GET` `/api/query/sql` 获取查询SQL

|参数名|类型|含义|参数位置|是否必选|
|----|----|----|----|----|
|type|str|数据库类型|URL|√|
|sql|str|SQL 语句，标准SQL|URL|√|
|schema|str|数据库名|URL||

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/api/query/sql?sql=SELECT+*+FROM+faker91+limit+10&type=oracle'
curl -i -X GET 'http://127.0.0.1:8000/api/query/sql?sql=SELECT+age,sum(age)+over(order+by+age)+FROM+faker91&type=mysql'
```
结果返回：

```json
{"sql": "SELECT *  FROM (SELECT *  FROM faker91)  WHERE ROWNUM <= 10"}
{"sql": "SELECT age, (SELECT sum(age) AS sum_1  FROM faker91 AS tb_ad1f41  WHERE tb_ad1f41.age <= faker91.age) AS fd_7e4a47  FROM faker91"}
```

#### `GET` `/api/query/tree` 获取查询语法树

|参数名|类型|含义|参数位置|是否必选|
|----|----|----|----|----|
|sql|str|SQL 语句，标准SQL|URL|√|

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/api/query/tree?sql=SELECT+*+FROM+faker91+limit+10'
```
结果返回：

```json
{"tree": {"query": {"windowDecls": {"list": [], "pos": {"columnNumber": 1, "endLineNumber": 1, "endColumnNumber": 21, "lineNumber": 1}}, "keywordList": {"list": [], "pos": {"columnNumber": 1, "endLineNumber": 1, "endColumnNumber": 6, "lineNumber": 1}}, "from": {"pos": {"columnNumber": 15, "endLineNumber": 1, "endColumnNumber": 21, "lineNumber": 1}, "names": ["faker91"], "componentPositions": [{"columnNumber": 15, "endLineNumber": 1, "endColumnNumber": 21, "lineNumber": 1}]}, "selectList": {"list": [{"pos": {"columnNumber": 8, "endLineNumber": 1, "endColumnNumber": 8, "lineNumber": 1}, "names": [""], "componentPositions": [{"columnNumber": 8, "endLineNumber": 1, "endColumnNumber": 8, "lineNumber": 1}]}], "pos": {"columnNumber": 8, "endLineNumber": 1, "endColumnNumber": 8, "lineNumber": 1}}, "pos": {"columnNumber": 1, "endLineNumber": 1, "endColumnNumber": 21, "lineNumber": 1}}, "fetch": {"scale": 0, "isExact": true, "pos": {"columnNumber": 29, "endLineNumber": 1, "endColumnNumber": 30, "lineNumber": 1}, "value": 10, "typeName": "DECIMAL", "prec": 2}, "pos": {"columnNumber": 29, "endLineNumber": 1, "endColumnNumber": 30, "lineNumber": 1}}}
```


### TodoList

* 数据分析
* 数据导出
* 可视化界面