from django.db import models
from django.contrib.auth.models import User


# 实例信息
class InstanceInfo(models.Model):
    class Meta:
        abstract = False
        db_table = 'instance_info'
        app_label = 'api'
        ordering = ('instance_name', 'apply_time',)
        indexes = [
            models.Index(fields=['instance_name']),
        ]

    # 创建用户ID
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # 实例类型 (redis or mysql)
    instance_type = models.CharField(max_length=8)
    # 实例名称 (uuid 生成)
    instance_name = models.CharField(max_length=36)
    # 实例信息
    instance_configuration = models.JSONField(null=True)
    # 实例状态
    instance_status = models.CharField(max_length=16)

    # 申请时间
    apply_time = models.DateTimeField(null=True)


# 端口信息
class InstancePort(models.Model):
    class Meta:
        abstract = False
        db_table = 'instance_port'
        app_label = 'api'
        ordering = ('port',)
        indexes = [
            models.Index(fields=['port']),
        ]

    # 实例信息
    instance_info = models.ForeignKey(InstanceInfo, on_delete=models.CASCADE, null=True)

    # port
    port = models.IntegerField()
    # 占用情况
    status = models.CharField(max_length=10, default='free')
