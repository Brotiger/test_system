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
from datetime import datetime
from pymongo import MongoClient
from select import select

class metaServer:

	__socket_port = None
	__queue = None

	__db_ip = None
	__db_port = None
	__db_name = None
	__db_collection = None

	__db = None
	__db_connection = None
	__db_posts = None

	__to_monitor = []

	__client_socket = None
	__addr = None

	def __init__(self, socket_port = 9090, queue = 999, db_ip = "127.0.0.1", db_port = 27018, db_name = "meta-database-test", db_collection = "meta-collection-test"):
		if(type(socket_port is int) and type(queue is int) and type(db_ip is str) and type(db_port is int) and type(db_name is str) and type(db_collection is str)):
			self.__socket_port = socket_port
			self.__queue = queue
			self.__db_ip = db_ip
			self.__db_port = db_port
			self.__db_name = db_name
			self.__db_collection = db_collection
		else:
			raise Exception("metaServer - invalid types passed to the constructor")

	#Запуск сервера
	def start(self):
		self.startDbServer()

		self.db_connection()

		server_socket = socket.socket()
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server_socket.bind(("",self.__socket_port))
		server_socket.listen(self.__queue)

		self.__to_monitor = [server_socket]

		print("socket start")

		while True:

			for s_err in self.__to_monitor: #фикс бага с сокетом имеющим отрицательный дескриптор, если дескриптор отрицательный - удаляем сокет из масива сокетов
				if s_err.fileno() == -1:
					self.__to_monitor.remove(s_err)

			ready_to_read, _, _ = select(self.__to_monitor, [], []) #read, write, errors

			for sock in ready_to_read:
				if sock is server_socket:
					self.__accept_connection(sock)
				else:
					self.__read_message(sock)

	def __read_message(self, client_socket):
		data = client_socket.recv(1024)

		if data:
			client_socket.send("success".encode())
			data_obj = pickle.loads(data)
			data_obj["IP"] = self.__addr
			data_obj["time_stamp"] = datetime.today().timestamp()
			self.__post(data_obj)
			print("Data fron user: " + self.__addr + " received")
		else:
			client_socket.close()
			print("Connection whith user: " + self.__addr + " is broken")

	def __accept_connection(self, server_socket):
		self.__client_socket, addr = server_socket.accept()
		self.__addr = addr[0]

		self.__to_monitor.append(self.__client_socket)

		print("Connection with user: " + self.__addr + " established")

	def __post(self, obj):
		post_id = self.__db_posts.update({"IP": obj["IP"]}, obj, upsert = True)

	#вывод всех записей в DB
	def showDB(self):
		if(self.__db_posts != None):
			for post in self.__db_posts.find():
				pp(post)
		else:
			raise Exception("metaServer - it is impossible to request information output from DB without connecting to it, please call db_connection () function first")

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

	#подключение к DB
	def db_connection(self):
		client = MongoClient(self.__db_ip, self.__db_port)
		self.__db = client[self.__db_name]
		self.__db_collection = self.__db[self.__db_collection]
		self.__db_posts = self.__db.posts

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

	#Запуск сервера DB
	def startDbServer(self):
		result = subprocess.Popen(["mongod","--port", str(self.__db_port)], stdout=subprocess.PIPE)

		print("Db server start")

'''Пример использования'''
server = metaServer()
server.start()
#server.db_connection()
#server.showDB()