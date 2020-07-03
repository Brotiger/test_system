#!/usr/bin/python3

'''
 Название: Программа для определения производительности узла theool;
 Автор: Берестнев Дмитрий Дмитриевич;
 Необходимые программы: python3, pip3, gcc, python3-dev, smartmontools, dd;
 Необходимые библиотеки: pp-ez, psutil;
'''

import os
import psutil
import pp
import re
import subprocess
import random
import string
import socket
import pickle

class sysTest:
	#точка монтирования дисков перед проверкой
	__mount_point = "/mnt/sys_test/"
	__server_ip = "127.0.0.1"
	__server_port = 9090
	__test_pass = False
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
	        'slab': None,
	    },
	    "swap": {
	    	'total': None,
	    	'used': None,
	    	'free': None,
	    },
	    "cpu": {
	        'all_cores': None,
	        'cores': None,
	        'freq': {
	            'current': None,
	            'min': None,
	            'max': None,
	        },
	    },
	}

	def __buildblock(self, size):
		return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(size))

	#добавление масива с защищенными разделами
	def setPP(self, pp_arr):
		if(type(pp_arr is list)):
			self.__partition_protection = pp_arr
			return True
		return False

	#получение масива с защищенными разделами
	def getPP(self):
		return self.__partition_protection

	#изменение точки монтирования для дисков
	def setMP(self, path):
		if(type(path is str)):
			self.__mount_point = path
			return True
		return False

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

		self.__test_pass = True

		return True;

	def __findPartitionsAndDisks(self):

		dev_arr = os.listdir(path="/dev/")

		for disk in dev_arr:
			disk_info = {
				"smart": False,
				"serial_number": None,
				"device": None,
				"size": None,
				"partitions": {},
			}
			obg_d = re.search("^sd[a-z]{1}$", disk)
			if(obg_d != None):
				disk_info["device"] = disk
				disk_full_info = subprocess.Popen(["smartctl","-i","/dev/" + disk], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				d_out, d_err = disk_full_info.communicate()
				d_out_obj = self.__comandResultToObject(d_out)

				disk_info["serial_number"] = d_out_obj["Serial Number"]
				disk_info["size"] = int(float(re.search("\d{0,},{0,}\d{0,} GB",d_out_obj["User Capacity"]).group(0).split(" ")[0].strip().replace(",",".")))
				disk_info["smart"] = self.__smartTest(disk)
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
								pw_out = self.__parseSpeed(pw_out)
								
								partition_info["write_speed"] = pw_out

								#попытка чтения
								partition_read_speed = subprocess.Popen(['dd', "if=" + self.__mount_point + partition + "/" + temp_file,'of=/dev/null','bs=1M','count=1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
								
								pr_out,ps_err = partition_read_speed.communicate()
								pr_out = self.__parseSpeed(pr_out)

								partition_info["read_speed"] = pr_out
								
								os.system("rm "+ self.__mount_point + partition + "/" + temp_file)
							except:
								partition_info["write_speed"] = False
								partition_info["read_speed"] =  False

						partition_info["percent"] = current_drive.percent
						os.system("umount " + self.__mount_point + partition)
						disk_info["partitions"][partition] = partition_info
				self.__test_result["disks"].append(disk_info)

	def __comandResultToObject(self, result):
		result = str(result)
		result = result.split("\\n")
		result = result[4:]
		result = result[0:-2]
		result_obj = {}
		i = 0;
		for param in result:
			key_value = param.split(":")
			result_obj[key_value[0]] = key_value[1].strip()
			i = i + 1
		return result_obj

	def __parseSpeed(self, speed_byt):
		speed_str = str(speed_byt)
		speed_str = re.sub(".{0,} copied, ", "", speed_str)
		speed_str = re.split(" s, ", speed_str)[0]
		return speed_str

	def __smartTest(self, disk):
		smart_comand = subprocess.Popen(["smartctl", "-H", "/dev/" + disk], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		s_out,s_err = smart_comand.communicate()
		s_out_obj = self.__comandResultToObject(s_out)

		if(s_out_obj["SMART overall-health self-assessment test result"] == "PASSED"):
			return True
		return False

	#возвращение данных о железе в виде объекта
	def getObj(self):
		return self.__test_result

	#возвращение данных о железе в формате JSON 
	def getJson(self):
		return pickle.dumps(self.__test_result)

	#вывод данных в консоль
	def printArr(self):
		pp(self.__test_result)

	#отправка данных на мета сервер
	def send(self):
		if(self.__test_pass):
			sock = socket.socket()
			sock.connect((self.__server_ip, self.__server_port))
			sock.send(self.getJson())
			data = sock.recv(1024)
			if(data.decode() == "success"):
				sock.close()
				return True
		return False

	#установка IP сервера
	def setIP(self, ip):
		if(type(ip is str)):
			self.__server_ip = ip
			return True
		return False

	#установка порта сервера
	def setPost(self, port):
		if(type(port is int)):
			self.__server_port = port
			return True
		return False

'''Пример использования'''
test = sysTest()
test.test()
test.printArr()
test.send()