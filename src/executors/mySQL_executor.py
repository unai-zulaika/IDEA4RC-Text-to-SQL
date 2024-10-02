import mysql.connector
import time
from premsql.executors.base import BaseExecutor


class MySQLExecutor(BaseExecutor):
    def execute_sql(self, sql: str, dsn_or_db_path: str) -> dict:
        # Connect to the database using pg8000
        # TODO: load from ENV
        conn = mysql.connector.connect(
            host="localhost",
            user="idea4rc_llm",
            password="test@123",
            database="idea4rc_dm",
        )
        cursor = conn.cursor()

        start_time = time.time()
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            error = None
        except Exception as e:
            result = None
            error = str(e)

        end_time = time.time()
        cursor.close()
        conn.close()

        result = {
            "result": result,
            "error": error,
            "execution_time": end_time - start_time,
        }
        return result
