import sqlite3
from os import path,getcwd

db=path.join(getcwd(), 'database.db')
class Database:
    def __init__(self):
        self.connection = sqlite3.connect(db)

    def query(self, query, arg=()):
        self.connection = sqlite3.connect(db)
        cursor = self.connection.cursor()
        cursor.execute(query, arg)
        results=cursor.fetchall()
        cursor.close()
        return results;

    def insert(self, query, args={}):
        self.connection = sqlite3.connect(db)
        cursor = self.connection.cursor()
        cursor.execute(query, args)
        self.connection.commit()
        result = cursor.lastrowid
        cursor.close()
        return result


    def just_execute(self, query, arg=()):
        self.connection = sqlite3.connect(db)
        cursor = self.connection.cursor()
        cursor.execute(query, arg)
        self.connection.commit()
        cursor.close()
        return True;