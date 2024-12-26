from agents.core import Agent

class FeedbackCollectorAgent(Agent):
    def __init__(self, model_id: str):
        super().__init__(model_id)

    def request_feedback(self, variation: dict, performance_data: dict) -> str:
        return "Feedback requested."

    def store_feedback(self, variation: dict, feedback: str) -> None:
        pass
