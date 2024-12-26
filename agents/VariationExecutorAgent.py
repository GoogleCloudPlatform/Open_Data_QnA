from agents.core import Agent

class VariationExecutorAgent(Agent):
    def __init__(self, model_id: str):
        super().__init__(model_id)

    def execute_campaign(self, variation: dict) -> dict:
        return {"status": "success"}
