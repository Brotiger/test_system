#!/usr/bin/python3

'''
	Название: mongoPost;
	Описание: Программа предоставляет список узлов определенного класса;
	Автор: Берестнев Дмитрий Дмитриевич;
	Необходимые программы: mongodb;
	Необходимые библиотеки: pymongo;
'''

import pp
from pymongo import MongoClient

class mongoPost:

	__class_types = ["A", "B", "C"]
	__db_ip = None
	__db_port = None
	__db_name = None
	__db_collection_name = None

	def __init__(self, db_ip = "127.0.0.1", db_port = 27018, db_name = "meta-database-test", db_collection_name = "meta-collection-test"):
		if(type(db_ip is str) and type(db_port is int) and type(db_name is str) and type(db_collection_name is str)):
			self.__db_ip = db_ip
			self.__db_port = db_port
			self.__db_name = db_name
			self.__db_collection_name = db_collection_name
			self.db_connection()
		else:
			raise Exception("MongoPost - invalid types passed to the constructor")

	#Получение набора записей по классу
	def getByClass(self, act, obj_class):
		type_p = self.__class_types.index(obj_class)
		size = int(self.__db_posts.count() / len(self.__class_types))
		skip = type_p * size
		if(self.__db_posts != None):
			if(act == "read"):
				#self.__db_posts.find().sort({read_speed: 1}) #read spead у конкретного объекта
			elseif(act == "write"):
				self.__db_posts.find().sort({write_speed: 1})
			'''for post in self.__db_posts.find():
				pp(post)'''
		else:
			raise Exception("metaServer - it is impossible to request information output from DB without connecting to it, please call db_connection () function first")
	#Соединение с DB
	def db_connection(self):
		client = MongoClient(self.__db_ip, self.__db_port)
		self.__db = client[self.__db_name]
		self.__db_collection = self.__db[self.__db_collection_name]
		self.__db_posts = self.__db.posts

		print("Db connection")

	#Установка IP базы данных
	def setDbIp(self, ip):
		if(type(ip is str)):
			self.__db_ip = ip
			return True
		return False

	#Установка порта на котором работает база данных
	def setDbPort(self, port):
		if(type(port is int)):
			self.__db_port = port
			return True
		return False

	#Установка имени базы данных
	def setDbName(self, name):
		if(type(name is str)):
			self.__db_name = name
			return True
		return False

	#Установка имени колекции
	def setCollectionName(self, name):
		if(type(name is str)):
			self.__db_collection_name = name
			return True
		return False

'''Пример использования'''

mongoPost = mongoPost()
mongoPost.getByClass("read","A")