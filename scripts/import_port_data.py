# import port data
# python manage.py runscript import_port_data --script-args <port_start> <port_end>
from api.models import InstancePort


def run(*args):
    # 预先写入端口信息到数据库
    for port in range(int(args[0]), int(args[1]) + 1):
        if InstancePort.objects.filter(port=port).count() == 0:
            a = InstancePort(port=port)
            a.save()
