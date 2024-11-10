from functools import lru_cache
from typing import Annotated
import time

import psycopg2

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents import Text2SQLAgent
from text2sql_generators.text2SQL_generator_custom_HF import Text2SQLGeneratorCustomHF
from executors.mySQL_executor import MySQLExecutor
from evaluator import CustomText2SQLEvaluator
from prompt_generators import Text2SQLCustomPromptGenerator


from config import Settings


# TODO: move as args
inputs_path = "../inputs/queries.json"
term_to_code_path = "../dictionaries/code_to_term_variable.json"
instructions_path = "../inputs/instructions.txt"
ddl_statements_path = "../inputs/ddl_statements.txt"
# model_name = "premai-io/prem-1B-SQL"
model_name = "defog/llama-3-sqlcoder-8b"
# model_name = "meta-llama/Llama-3.2-1B-Instruct"
use_omop = True

#### prompt to be moved to generator
prompt_generator = Text2SQLCustomPromptGenerator(
    instructions_path=instructions_path,
    ddl_statements_path=ddl_statements_path,
    use_omop=use_omop,
)

# the generator is the the LLM that outputs the SQL
text2sql_generator = Text2SQLGeneratorCustomHF(
    model_name=model_name,
    experiment_name="test_generators",
    device="cuda:3",
    type="test",
    use_dspy=False,
)

# start the process that will run the SQL queries in the DB
executor = MySQLExecutor(use_omop=use_omop)

# Define the evaluator
evaluator = CustomText2SQLEvaluator(
    executor=executor, experiment_path=text2sql_generator.experiment_path
)

# the agent is an end to end class for running all the steps
agent = Text2SQLAgent(
    prompt_generator=prompt_generator,
    textsql_generator=text2sql_generator,
    executor=executor,
    evaluator=evaluator,
)


# Create FastAPI instance with custom docs and openapi url
app = FastAPI(docs_url="/api/docs")
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(
#     CORSMiddleware,
#     # Adjust this to specify allowed origins
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["POST"],
#     allow_headers=["*"],
# )


@lru_cache
def get_settings():
    return Settings()


@app.get("/api/query_to_sql")
def api_query_to_sql(
    settings: Annotated[Settings, Depends(get_settings)], query: str, api_key: str
):
    if settings.api_key != api_key:
        raise HTTPException(status_code=401, detail="Not authorized")

    results = agent.run_query(query=query)

    return results


@app.get("/api/perform_query")
def perform_query(
    settings: Annotated[Settings, Depends(get_settings)], query: str, api_key: str
):
    if settings.api_key != api_key:
        raise HTTPException(status_code=401, detail="Not authorized")

    error = None
    total_time = None
    result = None

    try:
        conn = psycopg2.connect(
            host=settings.HOST,
            database=settings.DATABASE,
            user=settings.USER_PG,
            password=settings.PASSWORD,
        )
        cursor = conn.cursor()
        start_time = time.time()

        cursor.execute(query)
        result = cursor.fetchall()
        end_time = time.time()
        cursor.close()
        conn.close()
        total_time = end_time - start_time

    except (Exception, psycopg2.DatabaseError) as error_raised:
        error = str(error_raised)

    result = {
        "result": result,
        "error": error,
        "execution_time": total_time,
    }

    return result
