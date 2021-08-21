# 项目需求
实现一个服务，该服务可以接收用户端请求，为用户申请 MySQL 与 Redis 两类资源。分配给用户的资源实例必须是真实、可以连接使用的。用户可以通过接口查看分配给自己的资源配置信息。

- 服务以 HTTP REST API 的方式提供接口，部分示例接口：

- 申请一个新的 MySQL/Redis 资源实例

- 查看某个实例的配置信息

- MySQL、Redis 服务可以在服务端用 Docker 容器启动，也可以使用其他方式

- 分配出的不同实例之间需要避免端口等资源冲突

- 资源的连接、鉴权等信息应该随机生成，部分必须的信息

- MySQL 连接地址、数据库名称、用户号、密码

- Redis 连接地址、密码  

加分项：

- 完整的项目架构图、项目安装、使用以及 README 文档

- MySQL 与 Redis 实例支持不同的个性化配置，比如：

- Redis 可以由用户设置数据最大占用空间

- MySQL 可以由用户设置数据库字符集

# 项目运行
# 预先安装

## Docker

1. docker安装 [https://docs.docker.com/engine/install/ubuntu/](https://docs.docker.com/engine/install/ubuntu/)  
2. 预先拉取mysql:5.7和redis:5.0.5镜像  
```plain
docker pull mysql:5.7 && docker pull redis:5.7 
```

## Python虚拟环境

我使用的是pyenv  

```plain
pyenv virtualenv 3.6.5 tencent
```

## 数据库

如果不想用自带的db.sqlite3的话，需要自己准备一个mysql或者postgresql数据库  

如果需要使用任务队列来创建实例的话，需要自己准备一个redis数据库  

## Git

安装git，因为项目用Github管理

# 项目安装

## 安装项目到本地

```plain
git clone https://github.com/austinzy/tencent.git .
```

## 
## 虚拟环境切换并且安装python依赖包  

```plain
cd ./tencent  
pyenv activate tencent  
pip install -r requirements.txt  
```

## 建立数据表

1. 如果不想用默认的db.sqlite3，在settings.py或者local_settings.py加入数据库信息
```plain
DATABASES = {
  'default': {
      'ENGINE': 'django.db.backends.postgresql_psycopg2', # 这是postgresql
      'NAME': '',  # 数据库名字
      'USER': '',  # 登录用户名
      'PASSWORD': '', # 登录密码
      'HOST': '',  # 数据库IP地址
      'PORT': '' # 数据库端口号
  }
}
```

2. 如果需要用任务队列来实现，修改setting.py或者local_settings.py的USE_QUEUE=True，并且加入Redis数据库信息
```plain
USE_QUEUE=True
  
# rq 配置
 RQ_QUEUES = {
  'default': {
      'HOST': '127.0.0.1',
      'PORT': 6379,
      'DB': 0,
      'DEFAULT_TIMEOUT': 3600,
      'PASSWORD': ''
  }
}
```

3. 数据库migrate
```plain
python manage.py migrate
```

4. 预先导入端口信息（我选的是10000～11000）

TODO：过滤已经被占用的端口

```plain
python manage.py runscript import_port_data --script-args <port_start> <port_end>
```

5. 创建用户用于后续登录（我选用的是tencent/tencent）
```plain
python manage.py createsuperuser
```

6. 启动后台API服务以及rqworker  
```plain
gunicorn -k gevent -t 0 -w 4 -b 0.0.0.0:5889 tencent.wsgi
python manage.py rqworker default
```

# 项目API说明
# 用户相关

## 登录

**链接**

```
/api/auth/login/
```
**请求**
```
POST
```
**请求字段**
|data 请求字段|类型|说明|
|:----:|:----|:----:|:----|:----:|:----|
|username|string|用户名|
|password|string|用户登录密码|

**返回结果示例**

**返回的是之后用来验证的Token**

```
{
    "2a27cf0ec22e79f7f11a912553399b601826ed59"
}
```

## 登出

**链接**

```
/api/auth/logout/
```
**请求**
```
POST
```
**请求字段**
|data 请求字段|类型|说明|
|:----:|:----|:----:|:----|:----:|:----|
|username|string|用户名|

**返回结果示例（已登录状态）**

```
{
    "detail": "Successfully logged out."
}
```
**返回结果示例（未登录状态）**
```
{
    "detail": "认证令牌无效。"
}
```

# 
# 创建容器

需要用户TOKEN

（authorization：Token 2a27cf0ec22e79f7f11a912553399b601826ed59）

**链接**

```
/api/create_ins/
```
**请求**
```
POST
```
**请求字段**
|data 请求字段|类型|说明|示例|
|:----:|:----|:----:|:----|:----:|:----|:----:|:----|
|*insType（必填）*|string|容器类型|redis/mysql|
|*meta（必填）*|dict|容器信息|{"databaseName": "test", "characterSetServer": "utf8mb4", "collationServer": "utf8mb4_unicode_ci", "maxSpace": "100m"}|

**返回结果示例（成功）**

```
{
    "detail": "实例创建完成"
}
{
    "detail": "开始创建实例"
}
```
**返回结果示例（失败）**
```
{
    "detail": "实例创建失败"
}
```

# 获取容器信息

需要用户TOKEN

（authorization：Token 2a27cf0ec22e79f7f11a912553399b601826ed59）

**链接**

```
/api/get_ins_info/
```
**请求**
```
POST
```
**请求字段**
|data 请求字段|类型|说明|示例|
|:----:|:----|:----:|:----|:----:|:----|:----|
|*insName（必填）*|string|容器名称|4416e3f2-21cc-4b36-867d-61a709643c5f|

**返回结果示例（成功）**

```
{
    "user_name": "tencent",
    "instance_type": "redis",
    "instance_name": "4416e3f2-21cc-4b36-867d-61a709643c5f",
    "instance_configuration": {
        "port": 10000,
        "password": "kXl3vPmiYsqw",
        "host": "192.168.51.20"
    },
    "apply_time": "2021-08-21T02:53:39.070933Z"
}
```
**返回结果示例（失败）**
```
{
    "detail": "此用户无此实例"
}
```

# 获取用户所有容器信息

需要用户TOKEN

（authorization：Token 2a27cf0ec22e79f7f11a912553399b601826ed59）

**链接**

```
/api/get_user_ins_info/
```
**请求**
```
POST
```
**请求字段**
**返回结果示例（成功）**

```
[
    {
        "user_name": "tencent",
        "instance_type": "redis",
        "instance_name": "4416e3f2-21cc-4b36-867d-61a709643c5f",
        "instance_configuration": {
            "port": 10000,
            "password": "kXl3vPmiYsqw",
            "host": "192.168.51.20"
        },
        "apply_time": "2021-08-21T02:53:39.070933Z"
    },
    {
        "user_name": "tencent",
        "instance_type": "redis",
        "instance_name": "3a016629-c615-4a26-bc25-7a2d84a45d2f",
        "instance_configuration": {
            "port": 10001,
            "password": "OuL5umYYkK2Y",
            "host": "192.168.51.20"
        },
        "apply_time": "2021-08-21T02:53:58.253973Z"
    }
]
```


# 项目截图
* 后端API服务  
![avatar](./images/后端API.png)
  
* rqworker服务 可以启动多个  
![avatar](./images/rqworker.png)  
  
* docker container  
![avatar](./images/docker_container.png)