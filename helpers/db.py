from helpers.database import db_connection

class DB():

    def __init__(self) -> None:
        pass

    def insert(self, table: str, columns: list, values: list):
        """
        Simplified method of making a MySQL connection and inserting values into a table
        """
        mydb = db_connection() # Establish DB connection
        cursor = mydb.cursor() # Initialize interaction with DB
        cols = ', ' .join(columns)
        vals = ''
        i = 0
        for val in values:
            i += 1
            if i == len(values):
                vals += f'"{val}"'
            else:
                vals += f'"{val}", '
        cursor.execute(f'INSERT INTO {table} ({cols}) VALUES ({vals})') # Execute DB command
        mydb.commit() # Commit above mentioned changes

    def select(table: str, columns: list, where: list = False, value: dict = False, amount: str = False):
        """
        Simplified method of making a MySQL connection and selecting values from a table
        """
        mydb = db_connection() # Establish DB connection
        cursor = mydb.cursor(buffered=True) # Initialize interaction with DB with buffered results
        if len(columns) > 1:
            cols = ', ' .join(columns) # Format columns
        else:
            cols = columns[0]
        if value and where:
            whereStatement = ''
            i = 0
            for val in where:
                i += 1
                if i == len(where): # Define if it is the last where statement
                    whereStatement += f'{val} = "{value[val]}"' # Format where statement
                else:
                    whereStatement += f'{val} = "{value[val]}" and ' # Format where statement
            cursor.execute(f'SELECT {cols} FROM {table} WHERE {whereStatement}') # Execute SQL statement 
        else:
            cursor.execute(f'SELECT {cols} FROM {table}') # Execute SQL statement 
        
        if amount and amount != 'all': # Determine type of result
            return cursor.fetchmany(int(amount))
        elif amount and amount == 'all':
            return cursor.fetchall()
        else:
            return cursor.fetchone()

    def update(self, table: str, columns: list, where: list, value: dict, values: dict = False):
        """
        Simplified method of making a MySQL connection and updating values in a table
        """
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
            if values[col] == 'None':
                values[col] = 'NULL'
                q = f'UPDATE {table} SET {col} = {values[col]} WHERE {whereStatement}'
            else:
                q = f'UPDATE {table} SET {col} = "{values[col]}" WHERE {whereStatement}'
            cursor.execute(q)

        mydb.commit()

    def delete(self, table: str, where: list, value: dict):
        """
        Simplified method of making a MySQL connection and deleting a cell from a table
        """
        mydb = db_connection()
        cursor = mydb.cursor()
        whereStatement = ''
        for val in where:
            if val == where[-1]:
                whereStatement += f'{val} = "{value[val]}" '
            else:
                whereStatement += f'{val} = "{value[val]}" and '
        cursor.execute(f'DELETE FROM {table} WHERE {whereStatement}')
        mydb.commit()