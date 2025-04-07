# from pathlib import Path
# import logging

# logger = logging.getLogger(__name__)

# def read_arbiter_prompt(prompt_name: str = "arbiter_prompt.txt") -> str:
#     """
#     Read the arbiter synthesis prompt template from the prompts directory.
#     """
#     return _read_prompt(prompt_name, get_default_arbiter_prompt)

# def get_default_arbiter_prompt() -> str:
#     """Fallback default arbiter prompt template"""
#     return """Evaluate these responses to: {prompt}

# {comparisons}

# Provide your response in EXACTLY this format:

# ### Combined Best Answer:
# [Your synthesized answer here]

# ### Confidence Score:
# [A numerical value between 0.00 and 1.00]

# ### Analysis of Differences:
# [Your analysis here]

# ### Dissenting Views:
# [Any dissenting opinions or alternative perspectives]

# ### Arbiter Model:
# Arbiter model: {arbiter}"""

# def read_iteration_prompt(prompt_name: str = "iteration_prompt.txt") -> str:
#     """
#     Read a prompt template from the prompts directory.
#     """
#     return _read_prompt(prompt_name, get_default_iteration_prompt)

# def get_default_iteration_prompt() -> str:
#     """Fallback default iteration prompt template"""
#     return """Context: {context}

# Question: {prompt}

# Provide your response in this exact format:

# ### Answer:
# [Your answer here]

# ### Confidence Score: 
# [A numerical value between 0.00 and 1.00]

# ### Model: {model}"""

# def read_system_prompt(prompt_name: str = "system_prompt.txt") -> str:
#     """
#     Read the system prompt template from the prompts directory.
#     """
#     return _read_prompt(prompt_name, get_default_system_prompt)

# def get_default_system_prompt() -> str:
#     """Fallback default system prompt template"""
#     return """You are an expert AI assistant trained to provide accurate and concise responses.
# Rules:
# - Be factual; cite sources when possible.
# - If unsure, say "I don't know".
# - Use markdown formatting."""

# def read_arbiter_system_prompt(prompt_name: str = "arbiter_system_prompt.txt") -> str:
#     """
#     Read the arbiter system prompt template from the prompts directory.
#     """
#     return _read_prompt(prompt_name, get_default_arbiter_system_prompt)

# def get_default_arbiter_system_prompt() -> str:
#     """Fallback default arbiter system prompt template"""
#     return """You are an arbitration AI that analyzes multiple responses.
# Rules:
# - Identify consensus and contradictions.
# - Highlight strong/weak arguments.
# - Provide a confidence score (0-1)."""

# def _read_prompt(prompt_name: str, default_func) -> str:
#     """
#     Generalized function to read a prompt template from the prompts directory.
#     Falls back to a default prompt if the file is not found or an error occurs.
#     """
#     try:
#         prompts_dir = Path(__file__).parent.parent / "prompts"
#         prompt_path = prompts_dir / prompt_name
        
#         if not prompt_path.exists():
#             raise FileNotFoundError(f"Prompt file {prompt_name} not found in {prompts_dir}")
        
#         with open(prompt_path, "r") as f:
#             return f.read().strip()
        
#     except Exception as e:
#         logger.error(f"Error loading prompt template {prompt_name}: {e}")
#         return default_func()
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def read_arbiter_prompt(prompt_name: str = "arbiter_prompt.txt") -> str:
    """
    Read the arbiter synthesis prompt template from the prompts directory.
    """
    return _read_prompt(prompt_name, get_default_arbiter_prompt)

def get_default_arbiter_prompt() -> str:
    """Fallback default arbiter prompt template"""
    return """Evaluate these responses to: {prompt}

{comparisons}

Provide your response in EXACTLY this format:

### Combined Best Answer:
[Your synthesized answer here]

### Confidence Score:
[A numerical value between 0.00 and 1.00]

### Analysis of Differences:
[Your analysis here]

### Dissenting Views:
[Any dissenting opinions or alternative perspectives]

### Arbiter Model:
Arbiter model: {arbiter}"""

def read_iteration_prompt(prompt_name: str = "iteration_prompt.txt") -> str:
    """
    Read a prompt template from the prompts directory.
    """
    return _read_prompt(prompt_name, get_default_iteration_prompt)

def get_default_iteration_prompt() -> str:
    """Fallback default iteration prompt template"""
    return """Context: {context}

Question: {prompt}

Provide your response in this exact format:

### Answer:
[Your answer here]

### Confidence Score: 
[A numerical value between 0.00 and 1.00]

### Model: {model}"""

def read_system_prompt(prompt_name: str = "system_prompt.txt") -> str:
    """
    Read the system prompt template from the prompts directory.
    """
    return _read_prompt(prompt_name, get_default_system_prompt)

def get_default_system_prompt() -> str:
    """Fallback default system prompt template"""
    return """You are an expert AI assistant trained to provide accurate and concise responses.
Rules:
- Be factual; cite sources when possible.
- If unsure, say "I don't know".
- Use markdown formatting."""

def read_arbiter_system_prompt(prompt_name: str = "arbiter_system_prompt.txt") -> str:
    """
    Read the arbiter system prompt template from the prompts directory.
    """
    return _read_prompt(prompt_name, get_default_arbiter_system_prompt)

def get_default_arbiter_system_prompt() -> str:
    """Fallback default arbiter system prompt template"""
    return """You are an arbitration AI that analyzes multiple responses.
Rules:
- Identify consensus and contradictions.
- Highlight strong/weak arguments.
- Provide a confidence score (0-1)."""

def read_iteration_prompt_sql(prompt_name: str = "iteration_prompt_sql.txt") -> str:
    """
    Read the SQL iteration prompt template from the prompts directory.
    """
    return _read_prompt(prompt_name, get_default_iteration_prompt_sql)

def get_default_iteration_prompt_sql() -> str:
    """Fallback default SQL iteration prompt template"""
    return """Context: {context}
            
Question: {prompt}
            
Provide your response in this exact format, in the "Answer" ONLY WRITE THE SQL Query:
            
### Answer:
[Your answer here]

### NLQ Intent:
[The Question/Prompt falls under which Data Retrival/Aggregation/Data Manipulation/Join & Relationship Logical Operations etc.]

### Confidence Score:
[A numerical value between 0.00 and 1.00]
            
### Model: {model}"""

def _read_prompt(prompt_name: str, default_func) -> str:
    """
    Generalized function to read a prompt template from the prompts directory.
    Falls back to a default prompt if the file is not found or an error occurs.
    """
    try:
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_path = prompts_dir / prompt_name
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file {prompt_name} not found in {prompts_dir}")
        
        with open(prompt_path, "r") as f:
            return f.read().strip()
        
    except Exception as e:
        logger.error(f"Error loading prompt template {prompt_name}: {e}")
        return default_func()
