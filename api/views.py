import json
import re
import uuid

from .models import InstanceInfo, InstancePort
from .utils import ins_creator

from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import django_rq


# 获取某个具体实例信息
class GetInstanceInfo(APIView):
    def post(self, request, *args, **kwargs):
        data_dict = request.data
        user = request.user

        try:
            ins_name = data_dict['insName']
            if not re.match(r'^[\da-zA-Z-]{36}$', ins_name):
                return Response({'detail': '实例名称错误'}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return Response({'detail': '缺少字段'}, status=status.HTTP_400_BAD_REQUEST)

        instance_info = InstanceInfo.objects.filter(instance_name=ins_name, user=user)
        if instance_info.count() > 0:
            res_instance_info = instance_info.first()
            res = {
                'user_name': user.username,
                'instance_type': res_instance_info.instance_type,
                'instance_name': res_instance_info.instance_name,
                'instance_configuration': res_instance_info.instance_configuration,
                # TODO 根据时区来返回时间
                'apply_time': res_instance_info.apply_time
            }
            return Response(res, status=status.HTTP_200_OK)
        else:
            return Response({'detail': '此用户无此实例'}, status=status.HTTP_400_BAD_REQUEST)


# 获取用户所有实例信息
class GetUserInstanceInfo(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user

        instance_data = InstanceInfo.objects.filter(user=user).order_by('apply_time')
        res = []
        for each_instance in instance_data:
            post = {
                'user_name': user.username,
                'instance_type': each_instance.instance_type,
                'instance_name': each_instance.instance_name,
                'instance_configuration': each_instance.instance_configuration,
                # TODO 根据时区来返回时间
                'apply_time': each_instance.apply_time
            }
            res.append(post)
        return Response(res, status=status.HTTP_200_OK)


# 创建实例
class CreateInstance(APIView):
    def post(self, request, *args, **kwargs):
        data_dict = request.data
        user = request.user
        try:
            ins_type = data_dict['insType']
            if not re.match(r'^(redis|mysql)$', ins_type):
                return Response({'detail': '此实例类型暂不支持'}, status=status.HTTP_400_BAD_REQUEST)
            # 端口被占用完了
            if InstancePort.objects.filter(status='free').count() == 0:
                return Response({'detail': '系统资源不足，无法创建新实例'}, status=status.HTTP_400_BAD_REQUEST)
            # meta 信息
            meta_data = json.loads(data_dict['meta'])
            ins_configuration = {}
            if ins_type == 'mysql':
                ins_configuration['mysql_database'] = meta_data['databaseName']
                # --character - set - server = utf8mb4 - -collation - server = utf8mb4_unicode_ci
                ins_configuration['character_set_server'] = meta_data.get('characterSetServer', '')
                ins_configuration['collation_server'] = meta_data.get('collationServer', '')
            elif ins_type == 'redis':
                ins_configuration['max_space'] = meta_data.get('maxSpace', '')
        except KeyError:
            return Response({'detail': '缺少字段'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成InstanceInfo数据
        ins_name = uuid.uuid4()
        ins_info = InstanceInfo(instance_name=ins_name, instance_status='queueing', instance_type=ins_type,
                                user=user, apply_time=timezone.now(), instance_configuration=ins_configuration)
        ins_info.save()
        if not getattr(settings, 'USE_QUEUE', False):
            try:
                ins_creator(ins_type, ins_name)
                return Response({'detail': '实例创建完成'}, status=status.HTTP_200_OK)
            except:
                return Response({'detail': '实例创建失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # 进入任务队列，等待创建
            django_rq.enqueue(ins_creator, ins_type=ins_type, ins_name=ins_name, job_timeout=600)

            return Response({'detail': '开始创建实例'}, status=status.HTTP_200_OK)
