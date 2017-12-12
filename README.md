# iQuey

数据仓库通用查询服务

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

### 数据库接口

#### `GET` `/api/databases` 获取全部数据库

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
curl -i -X GET 'http://127.0.0.1:8000/db/databases?type=mysql&host=127.0.0.1&port=3306&username=root&password=123456'
```
结果返回：

```json
{
    "databases": ["information_schema", "mysql", "performance_schema"]
}
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
|database|str|数据库名称|URL|√|
|kwargs|str - `json`|数据库其他配置参数|URL||

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/tables?type=mysql&host=127.0.0.1&port=3306&username=root&password=12345&database=mysql'
```
结果返回：

```json
{
    "tables": [{"type": "table", "name": "columns_priv"}, {"type": "table", "name": "db"}, {"type": "table", "name": "event"}, {"type": "table", "name": "func"}, {"type": "table", "name": "general_log"}, {"type": "table", "name": "help_category"}, {"type": "table", "name": "help_keyword"}, {"type": "table", "name": "help_relation"}, {"type": "table", "name": "help_topic"}, {"type": "table", "name": "host"}, {"type": "table", "name": "ndb_binlog_index"}, {"type": "table", "name": "plugin"}, {"type": "table", "name": "proc"}, {"type": "table", "name": "procs_priv"}, {"type": "table", "name": "proxies_priv"}, {"type": "table", "name": "servers"}, {"type": "table", "name": "slow_log"}, {"type": "table", "name": "tables_priv"}, {"type": "table", "name": "time_zone"}, {"type": "table", "name": "time_zone_leap_second"}, {"type": "table", "name": "time_zone_name"}, {"type": "table", "name": "time_zone_transition"}, {"type": "table", "name": "time_zone_transition_type"}, {"type": "table", "name": "user"}]
}
```


#### `GET` `/api/schema` 查看数据库表结构信息

|参数名|类型|含义|参数位置|是否必选|
|----|----|----|----|----|
|type|str|数据库类型|URL|√|
|host|str|数据库地址|URL|√|
|port|int|数据库端口|URL||
|username|str|数据库用户名|URL||
|password|str|数据库密码|URL||
|alias|str|数据库其他连接参数|URL||
|database|str|数据库名称|URL|√|
|table|str|数据表名称|URL|√|
|kwargs|str - `json`|数据库其他配置参数|URL||

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/schema?type=mysql&host=127.0.0.1&port=3306&username=root&password=123456&database=mysql&table=user'
```
结果返回：

```json
{
    {"columns": [{"default": "''", "type": "str", "name": "Host", "nullable": false}, {"default": "''", "type": "str", "name": "User", "nullable": false}, {"default": "''", "type": "str", "name": "Password", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Select_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Insert_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Update_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Delete_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Drop_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Reload_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Shutdown_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Process_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "File_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Grant_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "References_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Index_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Alter_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Show_db_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Super_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_tmp_table_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Lock_tables_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Execute_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Repl_slave_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Repl_client_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_view_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Show_view_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_routine_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Alter_routine_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_user_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Event_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Trigger_priv", "nullable": false}, {"default": "'N'", "type": "unicode", "name": "Create_tablespace_priv", "nullable": false}, {"default": "''", "type": "unicode", "name": "ssl_type", "nullable": false}, {"default": null, "type": "str", "name": "ssl_cipher", "nullable": false}, {"default": null, "type": "str", "name": "x509_issuer", "nullable": false}, {"default": null, "type": "str", "name": "x509_subject", "nullable": false}, {"default": "'0'", "autoincrement": false, "type": "int", "name": "max_questions", "nullable": false}, {"default": "'0'", "autoincrement": false, "type": "int", "name": "max_updates", "nullable": false}, {"default": "'0'", "autoincrement": false, "type": "int", "name": "max_connections", "nullable": false}, {"default": "'0'", "autoincrement": false, "type": "int", "name": "max_user_connections", "nullable": false}, {"default": "''", "type": "str", "name": "plugin", "nullable": true}, {"default": null, "type": "str", "name": "authentication_string", "nullable": true}]}
}
```

#### `GET` `/api/query/result` 获取查询结果

> 该接口依赖 PDBC 服务，生成 SQL 语法树

|参数名|类型|含义|参数位置|是否必选|
|----|----|----|----|----|
|type|str|数据库类型|URL|√|
|host|str|数据库地址|URL|√|
|port|int|数据库端口|URL||
|username|str|数据库用户名|URL||
|password|str|数据库密码|URL||
|alias|str|数据库其他连接参数|URL||
|database|str|数据库名称|URL||
|sql|str|SQL 语句，标准SQL|URL|√|
|kwargs|str - `json`|数据库其他配置参数|URL||

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/query/result?type=mysql&host=127.0.0.1&port=3306&username=root&password=123456&sql=select+*+from+test+limit+2'
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

> 该接口依赖 PDBC 服务，生成 SQL 语法树

|参数名|类型|含义|参数位置|是否必选|
|----|----|----|----|----|
|type|str|数据库类型|URL|√|
|sql|str|SQL 语句，标准SQL|URL|√|
|database|str|数据库名|URL||

##### 请求示例

```shell
curl -i -X GET 'http://127.0.0.1:8000/query/tree?sql=SELECT+*+FROM+faker91+limit+10'
```
结果返回：

```json
{"tree": {"query": {"windowDecls": {"list": [], "pos": {"columnNumber": 1, "endLineNumber": 1, "endColumnNumber": 21, "lineNumber": 1}}, "keywordList": {"list": [], "pos": {"columnNumber": 1, "endLineNumber": 1, "endColumnNumber": 6, "lineNumber": 1}}, "from": {"pos": {"columnNumber": 15, "endLineNumber": 1, "endColumnNumber": 21, "lineNumber": 1}, "names": ["faker91"], "componentPositions": [{"columnNumber": 15, "endLineNumber": 1, "endColumnNumber": 21, "lineNumber": 1}]}, "selectList": {"list": [{"pos": {"columnNumber": 8, "endLineNumber": 1, "endColumnNumber": 8, "lineNumber": 1}, "names": [""], "componentPositions": [{"columnNumber": 8, "endLineNumber": 1, "endColumnNumber": 8, "lineNumber": 1}]}], "pos": {"columnNumber": 8, "endLineNumber": 1, "endColumnNumber": 8, "lineNumber": 1}}, "pos": {"columnNumber": 1, "endLineNumber": 1, "endColumnNumber": 21, "lineNumber": 1}}, "fetch": {"scale": 0, "isExact": true, "pos": {"columnNumber": 29, "endLineNumber": 1, "endColumnNumber": 30, "lineNumber": 1}, "value": 10, "typeName": "DECIMAL", "prec": 2}, "pos": {"columnNumber": 29, "endLineNumber": 1, "endColumnNumber": 30, "lineNumber": 1}}}
```


### TodoList

* 数据导出
* 可视化界面