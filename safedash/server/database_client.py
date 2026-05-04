import os
import logging
import mysql.connector
from mysql.connector import Error
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DatabaseClient:
    def __init__(self):
        self.host = os.getenv("MYSQL_HOST", "db")
        self.port = int(os.getenv("MYSQL_PORT", 3306))
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "root")
        self.database = os.getenv("MYSQL_DATABASE", "safedash")
        self._connection = None

    def connect(self):
        try:
            self._connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self._connection.is_connected():
                logger.info("Successfully connected to MySQL database")
        except Error as e:
            logger.error(f"Error while connecting to MySQL: {e}")

    def disconnect(self):
        if self._connection and self._connection.is_connected():
            self._connection.close()
            logger.info("MySQL connection closed")

    def execute_query(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query and returns the results as a list of dictionaries.
        """
        if not self._connection or not self._connection.is_connected():
            self.connect()

        try:
            cursor = self._connection.cursor(dictionary=True)
            # MySQL connector uses %s for parameterized queries instead of @pname
            # We need to replace @pname with %(pname)s for dictionary parameters
            mysql_sql = sql
            if params:
                for key in params.keys():
                    mysql_sql = mysql_sql.replace(f"@{key}", f"%({key})s")

            cursor.execute(mysql_sql, params or {})
            result = cursor.fetchall()
            cursor.close()
            
            # Convert non-serializable types like Decimal and datetime
            import decimal
            import datetime
            
            cleaned_result = []
            for row in result:
                cleaned_row = {}
                for k, v in row.items():
                    if isinstance(v, decimal.Decimal):
                        cleaned_row[k] = float(v)
                    elif isinstance(v, (datetime.date, datetime.datetime)):
                        cleaned_row[k] = v.isoformat()
                    else:
                        cleaned_row[k] = v
                cleaned_result.append(cleaned_row)
                
            return cleaned_result
        except Error as e:
            logger.error(f"Failed to execute query: {e}\nSQL: {sql}\nParams: {params}")
            raise Exception(f"Database execution error: {str(e)}")
