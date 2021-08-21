import string
import random

from .models import InstanceInfo, InstancePort

import docker
from django.conf import settings


# 生成密码
def gen_password(length):
    chars = string.ascii_letters + string.digits
    return ''.join([random.choice(chars) for _ in range(length)])  # 得出的结果中字符会有重复的
    # return ''.join(random.sample(chars, 15))#得出的结果中字符不会有重复的


# 统一实例创建方法
def ins_creator(ins_type, ins_name):
    instance_info = InstanceInfo.objects.get(instance_name=ins_name)
    try:
        instance_info.instance_status = 'processing'
        instance_info.save()
        if ins_type == 'redis':
            redis_ins_creator(instance_info)
        else:
            mysql_ins_creator(instance_info)
        instance_info.instance_status = 'finished'
        instance_info.save()
    except Exception as e:
        instance_info.instance_status = 'failed'
        instance_info.save()


# redis实例创建
def redis_ins_creator(ins_info):
    client = docker.from_env()
    # 实例配置信息
    ins_configuration = ins_info.instance_configuration
    # container name
    ins_name = ins_info.instance_name
    # 分配端口
    # 端口数据写入数据库
    a = InstancePort.objects.filter(status='free').first()
    container_port = a.port
    a.status = 'used'
    a.instance_info = ins_info
    a.save()
    # 分配密码
    redis_password = gen_password(12)
    # 生成container
    command_str = '--requirepass {}'.format(redis_password)
    if ins_configuration.get('max_space', '') != '':
        command_str += ' --maxmemory {}'.format(ins_configuration.get('max_space', ''))
    container = client.containers.run("redis:5.0.5", ports={'6379/tcp': ('0.0.0.0', container_port)},
                                      command=command_str, name=ins_name, detach=True)
    # 代表创建成功
    if container.status == 'created':
        # info 写入数据库
        ins_info.instance_configuration = {
            'port': container_port,
            'password': redis_password,
            'host': getattr(settings, 'HOST_IP', '127.0.0.1')
        }
        ins_info.save()
    else:
        # free端口分配
        a = InstancePort(instance_info=ins_info)
        a.status = 'free'
        a.instance_info = None
        a.save()
        raise Exception


# mysql实例创建
def mysql_ins_creator(ins_info):
    client = docker.from_env()
    # 实例配置信息
    ins_configuration = ins_info.instance_configuration
    # container name
    ins_name = ins_info.instance_name
    # 分配端口
    # 端口数据写入数据库
    a = InstancePort.objects.filter(status='free').first()
    container_port = a.port
    a.status = 'used'
    a.instance_info = ins_info
    a.save()
    # 分配ROOT密码
    mysql_root_password = gen_password(12)
    # 生成container
    command_str = ''
    if ins_configuration.get('character_set_server', '') != '':
        command_str += '--character-set-server={} '.format(
            ins_configuration.get('character_set_server', ''))
    if ins_configuration.get('collation_server', '') != '':
        command_str += '--collation-server={} '.format(
            ins_configuration.get('collation_server', ''))
    container = client.containers.run("mysql:5.7", ports={'3306/tcp': ('0.0.0.0', container_port)},
                                      environment={
                                          'MYSQL_ROOT_PASSWORD': mysql_root_password,
                                          'MYSQL_DATABASE': ins_configuration.get('mysql_database')
                                      },
                                      command=command_str,
                                      name=ins_name, detach=True)
    # 代表创建成功
    if container.status == 'created':
        # info 写入数据库
        ins_configuration['port'] = container_port
        ins_configuration['mysql_root_password'] = mysql_root_password
        ins_configuration['host'] = getattr(settings, 'HOST_IP', '127.0.0.1')
        ins_info.instance_configuration = ins_configuration
        ins_info.save()
    else:
        # free端口分配
        a = InstancePort(instance_info=ins_info)
        a.status = 'free'
        a.instance_info = None
        a.save()
        raise Exception
