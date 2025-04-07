# pricing.py

import pandas as pd

# Define model pricing (per 1K tokens)
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
    "gemini-2": {"input": 0.0001, "output": 0.0004},
    "o3-mini": {"input": 0.0011, "output": 0.0044}
}

AVG_INPUT_TOKENS = 500
AVG_OUTPUT_TOKENS = 300

def calculate_cost(models, iterations):
    """Calculate total cost based on models and iterations"""
    total_cost = 0
    cost_breakdown = []
    
    for model, instances in models:
        if model in MODEL_PRICING:
            input_cost = (MODEL_PRICING[model]["input"] * AVG_INPUT_TOKENS / 1000) * iterations * instances
            output_cost = (MODEL_PRICING[model]["output"] * AVG_OUTPUT_TOKENS / 1000) * iterations * instances
            model_total = input_cost + output_cost
            total_cost += model_total
            cost_breakdown.append({
                "Model": model,
                "Instances": instances,
                "Input Cost": f"${input_cost:.4f}",
                "Output Cost": f"${output_cost:.4f}",
                "Total": f"${model_total:.4f}"
            })
    
    return total_cost, pd.DataFrame(cost_breakdown)