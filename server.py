#!/usr/bin/python3

'''
	Название: Программа отвечающая за принятие данных о производительности узла theool и определение его класса;
	Автор: Берестнев Дмитрий Дмитриевич;
	Необходимые программы: mongodb;
	Необходимые библиотеки: pymongo;
'''

import socket
import subprocess
import pp
import pickle
import datetime
from pymongo import MongoClient

class metaServer:

	__socket_port = None
	__queue = None

	__db_ip = None
	__db_port = None
	__db_name = None
	__db_collection = None

	__db_connection = None

	def __init__(self, socket_port = 9090, queue = 999, db_ip = "127.0.0.1", db_port = 27018, db_name = "meta-database", db_collection = "meta-collection"):
		if(type(socket_port is int) and type(queue is int) and type(db_ip is str) and type(db_port is int) and type(db_name is str) and type(db_collection is str)):
			self.__socket_port = socket_port
			self.__queue = queue
			self.__db_ip = db_ip
			self.__db_port = db_port
			self.__db_name = db_name
			self.__db_collection = db_collection
		else:
			raise Exception("metaServer в конструктор переданных данные не верных типов")

	#Запуск сервера
	def start(self):
		self.__startDbServer()

		self.__db_connection()

		__db = None

		sock = socket.socket()
		sock.bind(("",self.__socket_port))
		print("socket start")

		while True:
			sock.listen(self.__queue)
			conn, addr = sock.accept()

			print("connected", addr)

			while True:
				data = conn.recv(1024)
				if not data:
					break
				conn.send("success".encode())
				data_obj = pickle.loads(data)
				data_obj["IP"] = addr[0]
				self.__post(data_obj)
			conn.close()

	def __post(self, obj):
		posts = self.__db.posts
		post_id = posts.insert_one(obj).inserted_id
		for post in posts.find():
			pp(post)

	#Уставновка порта для прослушивания
	def setPort(self, port):
		if(type(port is int)):
			self.__socket_port = port
			return True
		return False

	#Установка размера очереди
	def setQueue(self, queue):
		if(type(queue is int)):
			self.__queue = queue
			return True
		return False

	def __db_connection(self):
		client = MongoClient(self.__db_ip, self.__db_port)
		self.__db = client[self.__db_name]
		self.__db_collection = self.__db[self.__db_collection]
		print("Db connection")

	#Установка IP базы данных
	def setDbIp(self, ip):
		if(type(ip is str)):
			self.__db_ip = ip
			return True
		return False

	#Установка порта на котором работает база данных
	def setDbIp(self, port):
		if(type(port is int)):
			self.__db_port = port
			return True
		return False

	#Установка имени базы данных
	def setDbIp(self, name):
		if(type(name is str)):
			self.__db_name = name
			return True
		return False

	#Установка имени колекции
	def setCollectionName(self, name):
		if(type(name is str)):
			self.__db_collection = name
			return True
		return False

	def __startDbServer(self):
		result = subprocess.Popen(["mongod","--port", str(self.__db_port)], stdout=subprocess.PIPE)
		print("Db server start")

server = metaServer()
server.start()