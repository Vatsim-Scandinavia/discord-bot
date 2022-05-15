

from datetime import date

from helpers.database import db_connection


class StaffingDB():

    def __init__(self) -> None:
        pass

    def insert(self, table: str, columns: list, values: list):
        mydb = db_connection()
        cursor = mydb.cursor()
        cols = ', ' .join(columns)
        vals = ''
        i = 0
        for val in values:
            i += 1
            if i == len(values):
                vals += f'"{val}"'
            else:
                vals += f'"{val}", '
        cursor.execute(f'INSERT INTO {table} ({cols}) VALUES ({vals})')
        mydb.commit()

    def select(self, table: str, columns: list, where: list = False, value: dict = False, amount: str = False):
        mydb = db_connection()
        cursor = mydb.cursor()
        if len(columns) > 1:
            cols = ', ' .join(columns)
        else:
            cols = columns[0]
        if value and where:
            whereStatement = ''
            i = 0
            for val in where:
                i += 1
                if i == len(where):
                    whereStatement += f'{val} = "{value[val]}"'
                else:
                    whereStatement += f'{val} = "{value[val]}" and '
            cursor.execute(f'SELECT {cols} FROM {table} WHERE {whereStatement}')
        else:
            cursor.execute(f'SELECT {cols} FROM {table}')
        
        if amount and amount != 'all':
            return cursor.fetchmany(int(amount))
        elif amount and amount == 'all':
            return cursor.fetchall()
        else:
            return cursor.fetchone()

    def update(self, table: str, columns: list, where: list, value: dict, values: dict = False):
        mydb = db_connection()
        cursor = mydb.cursor()
        whereStatement = ''
        i = 0
        for val in where:
            i += 1
            if i == len(where):
                whereStatement += f'{val} = "{value[val]}" '
            else:
                whereStatement += f'{val} = "{value[val]}" and '
        for col in columns:
            cursor.execute(f'UPDATE {table} SET {col} = "{values[col]}" WHERE {whereStatement}')
        mydb.commit()

    def delete(self, table: str, where: list, value: dict):
        mydb = db_connection()
        cursor = mydb.cursor()
        whereStatement = ''
        for val in where:
            if val == where[-1]:
                whereStatement += f'{val} = "{value[val]}" '
            else:
                whereStatement += f'{val} = "{value[val]}" and '
        cursor.execute(f'DELETE FROM {table} WHERE {whereStatement}"')
        mydb.commit()