# llm_consortium/utils/prompt_utils.py
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def read_iteration_prompt(prompt_name: str = "iteration_prompt.txt") -> str:
    """
    Read a prompt template from the prompts directory.
    
    Args:
        prompt_name (str): Name of the prompt template file
        
    Returns:
        str: Contents of the prompt template file
    """
    try:
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_path = prompts_dir / prompt_name
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file {prompt_name} not found in {prompts_dir}")
            
        with open(prompt_path, "r") as f:
            return f.read().strip()
            
    except Exception as e:
        logger.error(f"Error loading prompt template: {e}")
        return get_default_prompt()

def get_default_prompt() -> str:
    """Fallback default prompt template"""
    return """Context: {context}

Question: {prompt}

Provide your response in this exact format:

### Answer:
[Your answer here]

### Confidence Score: 
[A numerical value between 0.00 and 1.00]

### Model: {model}"""