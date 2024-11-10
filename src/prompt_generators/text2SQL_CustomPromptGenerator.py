class Text2SQLCustomPromptGenerator:
    def __init__(
        self,
        instructions_path: str,
        ddl_statements_path: str,
        use_omop: bool,
    ):
        self.use_omop = use_omop
        if not use_omop:
            self.ddl_statements = self.load_ddl_statements(
                ddl_statements_path=ddl_statements_path
            )
            self.instructions = self.load_instructions(
                instructions_path=instructions_path
            )
        else:
            self.ddl_statements = self.load_ddl_statements(
                ddl_statements_path=ddl_statements_path.replace(
                    "ddl_statements", "omop_ddl_statements"
                )
            )
            self.instructions = self.load_instructions(
                instructions_path=instructions_path.replace(
                    "instructions", "omop_instructions"
                )
            )

    def generate_prompts(self, user_queries: list):
        prompts = []

        for user_query in user_queries:

            prompt = f"""
            <|begin_of_text|><|start_header_id|>user<|end_header_id|>

            Generate a MYSQL query to answer this question: `{user_query}`
            {self.instructions}

            DLL statements:
            {self.ddl_statements}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

            The following SQL query best answers the question: `{user_query}`:
            ```sql
            """
            prompts.append(prompt)

        return prompts

    def load_instructions(self, instructions_path: str):
        # TODO: Handle errors
        with open(instructions_path, "r") as instructions_file:
            instructions = instructions_file.read()

        return instructions

    # TODO: handle different ddl statement generation
    def load_ddl_statements(self, ddl_statements_path: str):
        # TODO: Handle errors
        with open(ddl_statements_path, "r") as ddl_statements_file:
            ddl_statements = ddl_statements_file.read()

        return ddl_statements
