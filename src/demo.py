from agents import Text2SQLAgent
from text2sql_generators.text2SQL_generator_custom_HF import Text2SQLGeneratorCustomHF
from executors.mySQL_executor import MySQLExecutor
from evaluator import CustomText2SQLEvaluator
from prompt_generators import Text2SQLCustomPromptGenerator

# TODO: move as args
inputs_path = "../inputs/queries.json"
term_to_code_path = "../dictionaries/code_to_term_variable.json"
instructions_path = "../inputs/instructions.txt"
ddl_statements_path = "../inputs/ddl_statements.txt"
# model_name = "premai-io/prem-1B-SQL"
model_name = "defog/llama-3-sqlcoder-8b"
# model_name = "meta-llama/Llama-3.2-1B-Instruct"

#### prompt to be moved to generator
prompt_generator = Text2SQLCustomPromptGenerator(
    instructions_path=instructions_path, ddl_statements_path=ddl_statements_path
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
executor = MySQLExecutor()

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

results = agent.run(inputs_path=inputs_path, term_to_code_path=term_to_code_path)

print(results)
