#!/usr/bin/python3

'''
 Название: Программа определяющая производительность узла theool;
 Автор: Берестнев Дмитрий Дмитриевич;
 Требования: python3, pip3, gcc, python3-dev;
 Библиотеки: pp-ez, psutil;
'''

import os
import json
import psutil
import pp
import re
import subprocess
import random
import string

class sysTest:
	__mount_point = "/mnt/sys_test/"
	#массив разделов защищенных от записи
	__partition_protection = ["sda1"]
	__test_result = {
	    "disks": [],
	    "memory": {
	        'total': None,
	        'used': None,
	        'free': None,
	        'available': None,
	        'percent': None,
	        'active': None,
	        'inactive': None,
	        'buffers': None,
	        'cached': None,
	        'shared': None,
	        'slab': None
	    },
	    "swap": {
	    	'total': None,
	    	'used': None,
	    	'free': None
	    },
	    "cpu": {
	        'all_cores': None,
	        'cores': None,
	        'freq': {
	            'current': None,
	            'min': None,
	            'max': None,
	        }
	    }
	}
	def __buildblock(self, size):
		return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(size))

	#добавление масива с защищенными разделами
	def setPP(self, pp_arr):
		if(type(self.__partition_protection) is list):
			self.__partition_protection = pp_arr

	#получение масива с защищенными разделами
	def getPP(self):
		return self.__partition_protection

	#изменение точки монтирования для дисков
	def setMP(self, path):
		if(type(self.__partition_protection) is str):
			self.__mount_point = path

	#сбор информации о железе
	def test(self):
		swap = psutil.swap_memory()
		mem = psutil.virtual_memory()
		freq = psutil.cpu_freq()
		all_cores = psutil.cpu_count()
		cores = psutil.cpu_count(logical = False)

		self.__test_result["swap"]["total"] = swap.total
		self.__test_result["swap"]["used"] = swap.used
		self.__test_result["swap"]["free"] = swap.free

		self.__test_result["memory"]["total"] = mem.total
		self.__test_result["memory"]["used"] = mem.used
		self.__test_result["memory"]["free"] = mem.free
		self.__test_result["memory"]["available"] = mem.available
		self.__test_result["memory"]["percent"] = mem.percent
		self.__test_result["memory"]["active"] = mem.active
		self.__test_result["memory"]["inactive"] = mem.inactive
		self.__test_result["memory"]["buffers"] = mem.buffers
		self.__test_result["memory"]["cached"] = mem.cached
		self.__test_result["memory"]["shared"] = mem.shared
		self.__test_result["memory"]["slab"] = mem.slab

		self.__test_result["cpu"]['freq']['current'] = freq.current
		self.__test_result["cpu"]['freq']['min'] = freq.min
		self.__test_result["cpu"]['freq']['max'] = freq.max

		self.__test_result["cpu"]["all_cores"] = all_cores
		self.__test_result["cpu"]["cores"] = cores

		self.__findPartitionsAndDisks()

		return True;

	def __findPartitionsAndDisks(self):

		dev_arr = os.listdir(path="/dev/")

		for disk in dev_arr:
			disk_info = {
				"type": None,
				"smart": False,
				"serial": None,
				"device": None,
				"size": None,
				"time_write": None,
				"time_read": None,
				"partitions": {},
			}
			obg_d = re.search("^sd[a-z]{1}$", disk)
			if(obg_d != None):
				disk_info["device"] = disk
				for partition in dev_arr:
					partition_info = {}
					if(re.match("^" + disk + "[0-8]{1}$", partition)):
						os.makedirs(self.__mount_point + partition, mode=0o777, exist_ok=True)
						os.system("mount /dev/"+partition+" " + self.__mount_point + partition)
						current_drive = psutil.disk_usage(self.__mount_point + partition)
						partition_info["total"] = current_drive.total
						partition_info["used"] = current_drive.used
						partition_info["free"] = current_drive.free
						if not partition in self.__partition_protection:
							temp_file = self.__buildblock(30)

							try:
								#попытка записи
								partition_write_speed = subprocess.Popen(['dd', "if=/dev/zero",'of=' + self.__mount_point + partition + "/" + temp_file,'bs=1M','count=1',"conv=fdatasync"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

								pw_out,ps_err = partition_write_speed.communicate()
								pw_out = str(pw_out)
								pw_out = re.sub(".{0,} copied, ", "", pw_out)
								pw_out = re.split(" s, ", pw_out)[0]
								partition_info["write_speed"] = pw_out

								#попытка чтения
								partition_read_speed = subprocess.Popen(['dd', "if=" + self.__mount_point + partition + "/" + temp_file,'of=/dev/null','bs=1M','count=1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
								pr_out,ps_err = partition_read_speed.communicate()
								pr_out = str(pr_out)
								pr_out = re.sub(".{0,} copied, ", "", pr_out)
								pr_out = re.split(" s, ", pr_out)[0]
								partition_info["read_speed"] = pr_out

								os.system("rm "+ self.__mount_point + partition + "/" + temp_file)
							except:
								partition_info["write_speed"] = False
								partition_info["read_speed"] =  False

						partition_info["percent"] = current_drive.percent
						os.system("umount " + self.__mount_point + partition)
						disk_info["partitions"][partition] = partition_info
				self.__test_result["disks"].append(disk_info)

	#возвращение данных о железе в виде объекта
	def getObj(self):
		return self.__test_result

	#возвращение данных о железе в формате JSON 
	def getJson(self):
		return json.dumps(self.__test_result)

	#вывод данных в консоль
	def printArr(self):
		pp(self.__test_result)

'''Пример использования'''
test = sysTest()
test.test()
test.printArr()