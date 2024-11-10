from typing import Optional
import os
from transformers import AutoTokenizer, AutoModelForCausalLM
from premsql.generators.base import Text2SQLGeneratorBase

import dspy


class Text2SQLGeneratorCustomHF(Text2SQLGeneratorBase):
    def __init__(
        self,
        model_name: str,
        experiment_name: str,
        type: str,
        device: str = "cuda:0",
        experiment_folder: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        use_dspy: bool = False,
    ):
        self.use_dspy = use_dspy
        if self.use_dspy:
            self.model = dspy.HFModel(model=model_name, hf_device_map="auto")
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
            ).to(device)
            # self.model.config.max_length = 8096
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token

        self.device = device
        self._api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.model_name = model_name
        super().__init__(
            experiment_folder=experiment_folder,
            experiment_name=experiment_name,
            type=type,
        )

    # Define your openai client
    @property
    def load_client(self):
        return self.model

    # Define the tokenizer
    @property
    def load_tokenizer(self):
        return self.tokenizer

    # Define the model name and path
    @property
    def model_name_or_path(self):
        return self.model_name

    # Write the generate function
    def generate(
        self,
        prompts: list,
        temperature: Optional[float] = 0.0,
        max_new_tokens: Optional[int] = 8096,
        postprocess: Optional[bool] = True,
        **kwargs
    ) -> str:

        if self.use_dspy:
            kwargs = {
                "temperature": 0.0,
                "do_sample": False,
                "padding": True,
                "return_tensors": "pt",
            }

            completion = self.model(prompt=prompts, kwargs=kwargs)  # DPSY

        else:
            # TODO: TRUNCATION!
            model_inputs = self.tokenizer(
                prompts,
                return_tensors="pt",
                padding=True,
                # max_length=max_new_tokens,
            ).to(self.device)

            generated_ids = self.model.generate(
                **model_inputs,
                temperature=0.0,
                do_sample=False,
                max_new_tokens=max_new_tokens
            )  # this for standard HF

            completion = self.tokenizer.batch_decode(
                generated_ids, skip_special_tokens=True
            )

        sql_statements = []

        for generated_text in completion:
            response = (
                self.postprocess(output_string=generated_text)
                if postprocess
                else completion
            )

            try:
                response = response.split("```sql", 1)[1]
                response = response.lstrip()
                response = response.replace("`", "")
                response = response.replace("NULLS LAST", "")
            except:
                pass

            index = response.find("SELECT")
            if index != -1:
                response = response[index:]

            sql_statements.append(response)

        return sql_statements
