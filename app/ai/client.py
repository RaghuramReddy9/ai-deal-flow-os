import json


class FakeLLMClient:
    def generate(self, prompt: str) -> str:
        mock_response = {
            "summary": "This appears to be a small business listing with limited but usable acquisition data. It may warrant review if the economics and recurring revenue profile hold up under diligence.",
            "industry": "Ecommerce",
            "recurring_revenue_signal": False,
            "risk_flags": ["limited financial detail", "unclear customer concentration"],
            "growth_potential": 3,
            "overall_score": 68,
            "score_reason": "Moderate opportunity with incomplete diligence data.",
        }
        return json.dumps(mock_response)