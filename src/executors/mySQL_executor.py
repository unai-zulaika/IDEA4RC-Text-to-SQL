import mysql.connector
import time
from premsql.executors.base import BaseExecutor
import psycopg2


class MySQLExecutor(BaseExecutor):
    def __init__(
        self,
        use_omop: bool,
    ):
        self.use_omop = use_omop

    def execute_sql(self, sql: str, dsn_or_db_path: str) -> dict:
        # Connect to the database using pg8000
        # TODO: load from ENV
        try:
            if self.use_omop:
                conn = psycopg2.connect(
                    "postgres://postgres:password@localhost:5432/omopcdm_synthetic"
                )

            else:
                conn = mysql.connector.connect(
                    host="localhost",
                    user="idea4rc_llm",
                    password="test@123",
                    database="idea4rc_dm",
                )

            cursor = conn.cursor()

            start_time = time.time()

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
