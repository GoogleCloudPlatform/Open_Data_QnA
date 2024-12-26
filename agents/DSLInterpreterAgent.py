from agents.core import Agent

class DSLInterpreterAgent(Agent):
    def __init__(self, model_id: str):
        super().__init__(model_id)

    def parse_dsl(self, dsl_string: str) -> dict:
        return {"channels": ["email"], "timing": "2 days later", "content": "Hello!"}

    def generate_variations(self, parsed_dsl: dict) -> list:
        return [parsed_dsl]
