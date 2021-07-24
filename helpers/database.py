import mysql.connector
from mysql.connector import Error
import os

_connection = None

def db_connection():

    global _connection

    if _connection is not None:
        return _connection

    try:
        _connection = mysql.connector.connect(
            host=os.getenv('BOT_DB_HOST'),
            user=os.getenv('BOT_DB_USER'),
            password=os.getenv('BOT_DB_PASSWORD'),
            database=os.getenv('BOT_DB_NAME'))

        if _connection.is_connected():
            print("[MySQL] Connected! Server version:", _connection.get_server_info())
            return _connection

    except Error as e:
        print("[MySQL] Error while connecting: ", e)
