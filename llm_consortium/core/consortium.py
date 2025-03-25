# import asyncio
# import sqlite3
# import threading
# import os
# from datetime import datetime
# from typing import List, Dict, Optional
# from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
# from openai import AsyncOpenAI
# from ..config.models import ConsortiumConfig, LogEntry
# from .logging import logger
# from ..utils.prompt_utils import read_iteration_prompt
# from ..utils.prompt_utils import read_arbiter_prompt
# from dotenv import load_dotenv
# import re
# load_dotenv()

# # Thread-local storage for SQLite connections
# thread_local = threading.local()

# class ConsortiumRunner:
#     def __init__(self):
#         self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         self.index = VectorStoreIndex.from_documents(SimpleDirectoryReader("data").load_data())
#         self.iteration_prompt_template = read_iteration_prompt()
#         self._init_db()

#     def _init_db(self):
#         """Initialize the database schema."""
#         conn = self._get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute('''CREATE TABLE IF NOT EXISTS interactions
#             (id INTEGER PRIMARY KEY AUTOINCREMENT,
#              timestamp DATETIME,
#              prompt TEXT,
#              model TEXT,
#              response TEXT,
#              confidence REAL,
#              latency REAL,
#              iteration INTEGER)''')
#         conn.commit()

#     def _get_db_connection(self):
#         """Get a thread-local SQLite connection."""
#         if not hasattr(thread_local, "conn"):
#             thread_local.conn = sqlite3.connect('consortium.db', check_same_thread=False)
#         return thread_local.conn

#     def _log_result(self, entry: LogEntry):
#         """Log a model response to the database."""
#         conn = self._get_db_connection()
#         cursor = conn.cursor()
#         cursor.execute('''INSERT INTO interactions
#             (timestamp, prompt, model, response, confidence, latency, iteration)
#             VALUES (?, ?, ?, ?, ?, ?, ?)''',
#             (entry.timestamp.isoformat(), entry.prompt, entry.model,
#              entry.response, entry.confidence, entry.latency, entry.iteration)
#         )
#         conn.commit()

#     async def _query_model(self, model: str, prompt: str, instance: int, iteration: int) -> LogEntry:
#         """Query a single model instance."""
#         start_time = datetime.now()
#         try:
#             # Get relevant context
#             query_engine = self.index.as_query_engine()
#             context = str(query_engine.query(prompt))
#             model_prompt = self.iteration_prompt_template.format(
#                 context=context,
#                 prompt=prompt,
#                 model=model
#             )
#             response = await self.client.chat.completions.create(
#                 model=model,
#                 messages=[{"role": "user", "content": model_prompt}],
#                 temperature=0.2
#             )

#             content = response.choices[0].message.content

#             return LogEntry(
#                 prompt=prompt,
#                 model=f"{model}-{instance}",
#                 response=self._extract_answer(content),
#                 confidence=self._extract_confidence(content),
#                 latency=(datetime.now() - start_time).total_seconds(),
#                 iteration=iteration
#             )
#         except Exception as e:
#             logger.error(f"Error querying model {model}: {str(e)}")
#             return LogEntry(
#                 prompt=prompt,
#                 model=f"{model}-{instance}",
#                 response=str(e),
#                 confidence=0.0,
#                 latency=(datetime.now() - start_time).total_seconds(),
#                 iteration=iteration
#             )
#     async def run_consortium(self, config: ConsortiumConfig, prompt: str) -> Dict:
#         responses = []
#         final_result = None

#         try:
#             for iteration in range(config.max_iterations):
#                 logger.info(f"Starting iteration {iteration + 1} of {config.max_iterations}")
#                 # Create tasks for all model instances
#                 tasks = [
#                     self._query_model(model, prompt, instance, iteration)
#                     for model, count in config.models.items()
#                     for instance in range(count)
#                 ]

#                 # Run all tasks concurrently
#                 results = await asyncio.gather(*tasks, return_exceptions=True)

#                 # Log results and handle exceptions
#                 for result in results:
#                     if isinstance(result, Exception):
#                         logger.error(f"Error in model query: {str(result)}")
#                         continue
#                     self._log_result(result)
#                     responses.append(result.to_dict())  # Convert LogEntry to dict

#                 # Synthesize responses using the arbiter model
#                 synthesis = await self._synthesize_responses(
#                     prompt, 
#                     [r for r in results if not isinstance(r, Exception)],
#                     config.arbiter
#                 )

#                 # Store the synthesis result
#                 final_result = {
#                     "synthesis": synthesis,
#                     "raw_responses": responses,  # List of dictionaries
#                     "iterations": iteration + 1
#                 }

#                 # Check if we should stop early
#                 if (synthesis['confidence'] >= config.confidence_threshold and
#                     iteration >= config.min_iterations - 1):
#                     logger.info(f"Stopping early at iteration {iteration + 1} (confidence threshold met)")
#                     break

#         except Exception as e:
#             logger.error(f"Error in consortium execution: {str(e)}")
#             raise

#         return final_result
    
#     async def _synthesize_responses(self, prompt: str, responses: List[LogEntry], arbiter: str) -> Dict:
#         """Synthesize responses using the arbiter model.
        
#         Args:
#             prompt: The original user prompt
#             responses: List of LogEntry objects containing model responses
#             arbiter: Name of the arbiter model to use
            
#         Returns:
#             Dict containing synthesized response components
#         """
#         # Format the model comparisons with their confidence scores
#         comparisons = "\n\n".join(
#             f"Model: {entry.model}\nConfidence: {entry.confidence:.2f}\nResponse:\n{entry.response}"
#             for entry in responses
#         )
        
#         # Load the arbiter prompt template
#         synthesis_template = read_arbiter_prompt()
#         synthesis_prompt = synthesis_template.format(
#             prompt=prompt,
#             comparisons=comparisons,
#             arbiter=arbiter
#         )
        
#         try:
#             # Query the arbiter model
#             response = await self.client.chat.completions.create(
#                 model=arbiter,
#                 messages=[{"role": "user", "content": synthesis_prompt}],
#                 temperature=0.2
#             )
#             content = response.choices[0].message.content
            
#             # Parse and return the structured response
#             return {
#                 "text": content,
#                 "confidence": self._extract_confidence(content),
#                 "analysis": self._extract_analysis(content),
#                 "dissenting_views": self._extract_dissent(content),
#                 "arbiter_model": arbiter
#             }
            
#         except Exception as e:
#             logger.error(f"Error in arbiter synthesis: {str(e)}")
#             return {
#                 "text": f"Error during synthesis: {str(e)}",
#                 "confidence": 0.0,
#                 "analysis": "",
#                 "dissenting_views": "",
#                 "arbiter_model": arbiter
#             }
#     def _extract_confidence(self, text: str) -> float:
#         """Extract confidence score from text using precise parsing."""
#         print(f"Raw LLM Response: {text}")  # Debugging Line

#         try:
#             match = re.search(r"### Confidence Score:\s*([0-9]\.[0-9]{2})", text, re.IGNORECASE)
#             if match:
#                 return float(match.group(1))
            
#             decimal_match = re.search(r"\b(0?\.\d{1,2}|1\.00)\b", text)
#             if decimal_match:
#                 return float(decimal_match.group())
            
#             percentage_match = re.search(r"(\d{1,3})%", text)
#             if percentage_match:
#                 return float(percentage_match.group(1)) / 100

#         except (ValueError, TypeError):
#             logger.warning("Could not parse confidence score, using default 0.0")
        
#         return 0.0  # Default if no match found


#     def _extract_analysis(self, text: str) -> str:
#         """Extract analysis section from text."""
#         return self._extract_section(
#             text, 
#             start_marker="### Analysis of Differences:", 
#             end_marker="### Dissenting Views:"
#         )

#     def _extract_dissent(self, text: str) -> str:
#         """Extract dissenting views section from text."""
#         return self._extract_section(
#             text, 
#             start_marker="### Dissenting Views:"
#         )
#     def _extract_answer(self, text: str) -> str:
#         """Extract the main answer from the model response."""
#         try:
#             match = re.search(r"### Answer:\s*(.*?)(?=\n###|$)", text, re.DOTALL)
#             if match:
#                 return match.group(1).strip()
#         except Exception:
#             logger.warning("Could not extract answer, returning full text")
#         return text.strip()  # Default to full response if parsing fails

#     def _extract_section(self, text: str, start_marker: str, end_marker: str = None) -> str:
#         """Generic section extractor helper."""
#         try:
#             start_idx = text.index(start_marker) + len(start_marker)
#             end_idx = text.index(end_marker) if end_marker else len(text)
#             return text[start_idx:end_idx].strip()
#         except ValueError:
#             logger.warning(f"Could not find section markers for {start_marker}")
#             return "No analysis available"