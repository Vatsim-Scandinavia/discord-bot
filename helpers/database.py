import mysql.connector
from mysql.connector import Error
import os
from helpers.config import BOT_DB_HOST, BOT_DB_PORT, BOT_DB_USER, BOT_DB_PASSWORD, BOT_DB_NAME

_connection = None

def db_connection():

    global _connection

    # Return connection
    if _connection is not None:

          # Check if connection is still alive
        try:
            _connection.ping(reconnect=False, attempts=3, delay=5)
        except mysql.connector.InterfaceError as err:
            print("[MySQL] Connection lost. Reconnecting...", flush=True)
            _connection = init_connection()

        return _connection
    else:
        _connection = init_connection()
        return _connection

def init_connection():

    global _connection

    try:
        _connection = mysql.connector.connect(
            host=BOT_DB_HOST,
            port=BOT_DB_PORT,
            user=BOT_DB_USER,
            password=BOT_DB_PASSWORD,
            database=BOT_DB_NAME
        )

        if _connection.is_connected():
            print("[MySQL] Connected! Server version:", _connection.get_server_info(), flush=True)
            return _connection

    except Error as e:
        print("[MySQL] Error while connecting: ", e, flush=True)