import json
import re
from typing import Optional
from term_matcher import load_term_to_code, match_terms_variable_names

from premsql.generators.base import Text2SQLGeneratorBase
from premsql.executors.base import BaseExecutor
from premsql.evaluator import Text2SQLEvaluator
from prompt_generators import Text2SQLCustomPromptGenerator


class Text2SQLAgent:
    def __init__(
        self,
        prompt_generator: Text2SQLCustomPromptGenerator,
        textsql_generator: Text2SQLGeneratorBase,
        executor: BaseExecutor,
        evaluator: Text2SQLEvaluator,
        experiment_folder: Optional[str] = None,
    ):
        self.prompt_generator = prompt_generator
        self.textsql_generator = textsql_generator
        self.executor = executor
        self.evaluator = evaluator

    def run_query(self, query: str):
        prompts = self.prompt_generator.generate_prompts(user_queries=[query])

        model_responses = self.textsql_generator.generate(
            prompts=prompts, temperature=0.0, max_new_tokens=512
        )

        return model_responses

    def run(self, inputs_path: str, term_to_code_path: str):
        # TODO
        modified_user_queries, sql_labels = self.prepare_inputs(
            inputs_path=inputs_path, term_to_code_path=term_to_code_path
        )

        prompts = self.prompt_generator.generate_prompts(
            user_queries=modified_user_queries
        )

        sql_statements = self.textsql_generator.generate(
            prompts=prompts, temperature=0.0, max_new_tokens=512
        )

        # join model's sql output and true labels

        model_responses = [
            {
                "modified_query": modified_query,
                "generated": response,
                "SQL": sql_labels,
                # "db_path": dsn_or_db_path,
            }
            for response, sql_labels, modified_query in zip(
                sql_statements, sql_labels, modified_user_queries
            )
        ]

        print(model_responses)

        # Now evaluate the models
        results = self.evaluator.execute(
            metric_name="accuracy",
            model_responses=model_responses,
            meta_time_out=5,
        )

        return results

    # TODO: preprocessing class?
    def prepare_inputs(self, inputs_path: str, term_to_code_path: str):
        # Opening JSON file
        queries_json = open(
            inputs_path,
        )

        # returns JSON object as
        # a dictionary
        user_inputs = json.load(queries_json)

        # Load term-to-code mappings
        term_to_code = load_term_to_code(
            term_to_code_path
        )  # if working with term to code
        modified_user_inputs = []
        sql_labels = []
        for user_input in user_inputs:
            # Match terms to codes
            user_query = user_input["question"]
            sql_labels.append(user_input["answer"])

            matched_json = match_terms_variable_names(
                user_query, term_to_code, threshold=50
            )
            # Match terms to codes
            modified_user_input = user_query

            for matched_words in matched_json:

                # TODO: review. terms should be codes. variable_name might be different?
                terms = ", ".join(
                    [match["term"] for match in matched_json[matched_words]]
                )
                vname = matched_json[matched_words][0]["variable_name"]
                replace_string = f"{vname} = {terms}"
                modified_user_input = modified_user_input.replace(
                    matched_words, replace_string
                )
            modified_user_inputs.append(modified_user_input)

        return modified_user_inputs, sql_labels
