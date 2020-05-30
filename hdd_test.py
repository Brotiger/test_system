#!/usr/bin/python3

'''
 Программа определяющая производительность узла theool

 Автор: Берестнев Дмитрий Дмитриевич

 Для нормальной работы необходим python3
 Для установки библиотек нужен пакетный менеджер pip3

 Для работы с диском нам понадобится библиотека atapt
 Команда для установки библиотеки:

 pip install atapt

 Для нормального вывода масивов и объектов понадобится библиотека pp
 Команда для установки данной библиотеки:

 pip install pp-ez

 Для получения информации об ОЗУ и CPU нам понадобится psutil
 Команды для установки данной библиотеки:

 apt-get install gcc python3-dev
 pip3 install psutil
'''
import json
import psutil
from atapt import atapt
import pp
import ctypes
import sys
import os
import re

str_test_result = ''
test_result = {
    "disks": [],
    "memory": {
        'total': None,
        'used': None,
        'free': None
    },
    "cpu": {
        'cores': None,
        'freq': {
            'current': None,
            'min': None,
            'max': None,
        }
    }
}

mem = psutil.virtual_memory()

test_result["memory"]["total"] = mem.total
test_result["memory"]["used"] = mem.used
test_result["memory"]["free"] = mem.free

freq = psutil.cpu_freq()

test_result["cpu"]['freq']['current'] = freq.current
test_result["cpu"]['freq']['min'] = freq.min
test_result["cpu"]['freq']['max'] = freq.max

cores = psutil.cpu_count()

test_result["cpu"]["cores"] = cores

dev_arr = os.listdir(path="/dev/")
partition_arr = []
usb_arr = []

for file in dev_arr:
    obg_p = re.search("^sd[a-z]{1}[0-9]{1}$", file)

    if(obg_p != None):
        partition_arr.append(obg_p.group(0))

for file in dev_arr:
    obg = re.search("^sd[a-z]{1}$", file)

    if(obg != None):

        dev = '/dev/' + obg.group(0)
        try:
            disk = atapt.atapt(dev) #ошибку сегментации вызывает эта функция
        except:
            usb_arr.append(dev)
            continue

        disk_info = {
            "type": None,
            "broken": False,
            "serial": None,
            "device": None,
            "size": None,
            "time_write": None,
            "time_read": None,
            "partitions": [],
        }

        for partition in partition_arr:
            if(re.match("^" + obg.group(0) + "[0-9]{1}$", partition)):
                partition_info = {
                    "name": None,
                }
                partition_info["name"] = partition
                os.makedirs("/mnt/test/"+partition, mode=0o777, exist_ok=True)
                os.system("mount /dev/"+partition+" /mnt/test/"+partition)
                disk_info["partitions"].append(partition_info)

        disk_info["serial"] = disk.serial
        disk_info["device"] = obg.group(0)
        disk_info["size"] = disk.size

        if disk.ssd:
            disk_info["type"] = "SSD";
        else:
            disk_info["type"] = "HDD";

        disk.timeout = 1000

        disk.runSmartSelftest(2)
        disk.readSmart()

        if disk.readSmartStatus() == atapt.SMART_BAD_STATUS:
            disk_info["broken"] = True
        else:
            count = 1
            disk.verifySectors(count, disk.sectors - 1)

            if(disk.ata_error != 00):
                disk_info["broken"] = True
            else:
                count = 1
                buf = ctypes.c_buffer(disk.logicalSectorSize * count)
                for i in range(disk.logicalSectorSize * count):
                    buf[i] = int(i % 128)
                disk.writeSectors(count, disk.sectors - 1, buf)

                if(disk.ata_error != 00):
                   disk_info["broken"] = True
                else:
                    disk_info["time_write"] = disk.duration

                    count = 1
                    disk.readSectors(count, disk.sectors - 1)
                    if(disk.ata_error == 00):
                        disk_info["time_read"] = disk.duration
                    else:
                        disk_info["broken"] = True
        test_result["disks"].append(disk_info)
str_test_result = json.dumps(test_result)
pp(test_result)
if usb_arr:
    print("\nСледующие устройства являются USB накопителями и не могут выступать в качестве хранилища для данных сети theool, если данные устройства являются внешними HDD или SDD накопителями, пожалуйста подключити их черзе SATA\n")
    pp(usb_arr)
    print()
sys.exit(0)