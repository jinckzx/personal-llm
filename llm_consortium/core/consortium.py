# import asyncio
# import sqlite3
# from datetime import datetime
# from typing import List, Dict
# from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
# from openai import AsyncOpenAI
# from llm_consortium.config.models import ConsortiumConfig, LogEntry
# from dotenv import load_dotenv
# import os
# load_dotenv()
# class ConsortiumRunner:
#     def __init__(self):
#         self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         self.index = VectorStoreIndex.from_documents(SimpleDirectoryReader("data").load_data())
#         self.conn = sqlite3.connect('consortium.db', check_same_thread=False)
#         self._init_db()
    
#     def _init_db(self):
#         cursor = self.conn.cursor()
#         cursor.execute('''CREATE TABLE IF NOT EXISTS interactions
#             (id INTEGER PRIMARY KEY AUTOINCREMENT,
#              timestamp DATETIME,
#              prompt TEXT,
#              model TEXT,
#              response TEXT,
#              confidence REAL,
#              latency REAL,
#              iteration INTEGER)''')
#         self.conn.commit()
#     async def run_consortium(self, config: ConsortiumConfig, prompt: str):
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
#                     "raw_responses": responses,
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
#     # async def run_consortium(self, config: ConsortiumConfig, prompt: str):
#     #     responses = []
#     #     for iteration in range(config.max_iterations):
#     #         tasks = [
#     #             self._query_model(model, prompt, instance, iteration)
#     #             for model, count in config.models.items()
#     #             for instance in range(count)
#     #         ]
#     #         results = await asyncio.gather(*tasks)
            
#     #         for result in results:
#     #             self._log_result(result)
            
#     #         synthesis = await self._synthesize_responses(
#     #             prompt, 
#     #             results,
#     #             config.arbiter
#     #         )
            
#     #         if synthesis['confidence'] >= config.confidence_threshold \
#     #         and iteration >= config.min_iterations - 1:
#     #             break
        
#     #     return {
#     #         "synthesis": synthesis,
#     #         "raw_responses": results,
#     #         "iterations": iteration + 1
#     #     }

#     async def _query_model(self, model: str, prompt: str, instance: int, iteration: int):
#         start_time = datetime.now()
#         try:
#             query_engine = self.index.as_query_engine()
#             context = str(query_engine.query(prompt))
            
#             response = await self.client.chat.completions.create(
#                 model=model,
#                 messages=[{
#                     "role": "user",
#                     "content": f"Context: {context}\n\nQuestion: {prompt}"
#                 }]
#             )
            
#             return LogEntry(
#                 prompt=prompt,
#                 model=f"{model}-{instance}",
#                 response=response.choices[0].message.content,
#                 confidence=self._extract_confidence(response.choices[0].message.content),
#                 latency=(datetime.now() - start_time).total_seconds(),
#                 iteration=iteration
#             )
#         except Exception as e:
#             return LogEntry(
#                 prompt=prompt,
#                 model=f"{model}-{instance}",
#                 response=str(e),
#                 confidence=0.0,
#                 latency=(datetime.now() - start_time).total_seconds(),
#                 iteration=iteration
#             )

#     def _log_result(self, entry: LogEntry):
#         cursor = self.conn.cursor()
#         cursor.execute('''INSERT INTO interactions
#             (timestamp, prompt, model, response, confidence, latency, iteration)
#             VALUES (?, ?, ?, ?, ?, ?, ?)''',
#             (entry.timestamp, entry.prompt, entry.model,
#              entry.response, entry.confidence, entry.latency, entry.iteration)
#         )
#         self.conn.commit()

#     async def _synthesize_responses(self, prompt: str, responses: List[LogEntry], arbiter: str):
#         comparisons = "\n".join(
#             f"{entry.model}:\n{entry.response}" 
#             for entry in responses
#         )
        
#         synthesis_prompt = f"""Evaluate these responses to: {prompt}
        
#         {comparisons}
        
#         Provide:
#         1. A combined best answer
#         2. Confidence score between 0-1
#         3. Brief analysis of differences"""
        
#         response = await self.client.chat.completions.create(
#             model=arbiter,
#             messages=[{"role": "user", "content": synthesis_prompt}],
#             temperature=0.2
#         )
        
#         content = response.choices[0].message.content
#         return {
#             "text": content,
#             "confidence": self._extract_confidence(content),
#             "analysis": self._extract_analysis(content)
#         }

#     def _extract_confidence(self, text: str) -> float:
#         return 0.9  # Simplified for example

#     def _extract_analysis(self, text: str) -> str:
#         return "Analysis placeholder"
# llm_consortium/core/consortium.py
# llm_consortium/core/consortium.py
import asyncio
import sqlite3
import threading
import os
from datetime import datetime
from typing import List, Dict, Optional
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from openai import AsyncOpenAI
from ..config.models import ConsortiumConfig, LogEntry
from .logging import logger
from dotenv import load_dotenv
load_dotenv()

# Thread-local storage for SQLite connections
thread_local = threading.local()

class ConsortiumRunner:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.index = VectorStoreIndex.from_documents(SimpleDirectoryReader("data").load_data())
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS interactions
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             timestamp DATETIME,
             prompt TEXT,
             model TEXT,
             response TEXT,
             confidence REAL,
             latency REAL,
             iteration INTEGER)''')
        conn.commit()

    def _get_db_connection(self):
        """Get a thread-local SQLite connection."""
        if not hasattr(thread_local, "conn"):
            thread_local.conn = sqlite3.connect('consortium.db', check_same_thread=False)
        return thread_local.conn

    def _log_result(self, entry: LogEntry):
        """Log a model response to the database."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO interactions
            (timestamp, prompt, model, response, confidence, latency, iteration)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (entry.timestamp.isoformat(), entry.prompt, entry.model,
             entry.response, entry.confidence, entry.latency, entry.iteration)
        )
        conn.commit()

    async def _query_model(self, model: str, prompt: str, instance: int, iteration: int) -> LogEntry:
        """Query a single model instance."""
        start_time = datetime.now()
        try:
            # Get relevant context
            query_engine = self.index.as_query_engine()
            context = str(query_engine.query(prompt))
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": f"Context: {context}\n\nQuestion: {prompt}"
                }]
            )
            
            return LogEntry(
                prompt=prompt,
                model=f"{model}-{instance}",
                response=response.choices[0].message.content,
                confidence=self._extract_confidence(response.choices[0].message.content),
                latency=(datetime.now() - start_time).total_seconds(),
                iteration=iteration
            )
        except Exception as e:
            logger.error(f"Error querying model {model}: {str(e)}")
            return LogEntry(
                prompt=prompt,
                model=f"{model}-{instance}",
                response=str(e),
                confidence=0.0,
                latency=(datetime.now() - start_time).total_seconds(),
                iteration=iteration
            )
    async def run_consortium(self, config: ConsortiumConfig, prompt: str) -> Dict:
        responses = []
        final_result = None

        try:
            for iteration in range(config.max_iterations):
                logger.info(f"Starting iteration {iteration + 1} of {config.max_iterations}")

                # Create tasks for all model instances
                tasks = [
                    self._query_model(model, prompt, instance, iteration)
                    for model, count in config.models.items()
                    for instance in range(count)
                ]

                # Run all tasks concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Log results and handle exceptions
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error in model query: {str(result)}")
                        continue
                    self._log_result(result)
                    responses.append(result.to_dict())  # Convert LogEntry to dict

                # Synthesize responses using the arbiter model
                synthesis = await self._synthesize_responses(
                    prompt, 
                    [r for r in results if not isinstance(r, Exception)],
                    config.arbiter
                )

                # Store the synthesis result
                final_result = {
                    "synthesis": synthesis,
                    "raw_responses": responses,  # List of dictionaries
                    "iterations": iteration + 1
                }

                # Check if we should stop early
                if (synthesis['confidence'] >= config.confidence_threshold and
                    iteration >= config.min_iterations - 1):
                    logger.info(f"Stopping early at iteration {iteration + 1} (confidence threshold met)")
                    break

        except Exception as e:
            logger.error(f"Error in consortium execution: {str(e)}")
            raise

        return final_result

    # async def run_consortium(self, config: ConsortiumConfig, prompt: str) -> Dict:
    #     """Run the consortium of models with the given configuration and prompt."""
    #     responses = []
    #     final_result = None

    #     try:
    #         for iteration in range(config.max_iterations):
    #             logger.info(f"Starting iteration {iteration + 1} of {config.max_iterations}")

    #             # Create tasks for all model instances
    #             tasks = [
    #                 self._query_model(model, prompt, instance, iteration)
    #                 for model, count in config.models.items()
    #                 for instance in range(count)
    #             ]

    #             # Run all tasks concurrently
    #             results = await asyncio.gather(*tasks, return_exceptions=True)

    #             # Log results and handle exceptions
    #             for result in results:
    #                 if isinstance(result, Exception):
    #                     logger.error(f"Error in model query: {str(result)}")
    #                     continue
    #                 self._log_result(result)
    #                 responses.append(result.to_dict())  # Convert LogEntry to dict

    #             # Synthesize responses using the arbiter model
    #             synthesis = await self._synthesize_responses(
    #                 prompt, 
    #                 [r for r in results if not isinstance(r, Exception)],
    #                 config.arbiter
    #             )

    #             # Store the synthesis result
    #             final_result = {
    #                 "synthesis": synthesis,
    #                 "raw_responses": responses,
    #                 "iterations": iteration + 1
    #             }

    #             # Check if we should stop early
    #             if (synthesis['confidence'] >= config.confidence_threshold and
    #                 iteration >= config.min_iterations - 1):
    #                 logger.info(f"Stopping early at iteration {iteration + 1} (confidence threshold met)")
    #                 break

    #     except Exception as e:
    #         logger.error(f"Error in consortium execution: {str(e)}")
    #         raise

    #     return final_result

    async def _synthesize_responses(self, prompt: str, responses: List[LogEntry], arbiter: str) -> Dict:
        """Synthesize responses using the arbiter model."""
        comparisons = "\n".join(
            f"{entry.model}:\n{entry.response}" 
            for entry in responses
        )
        
        synthesis_prompt = f"""Evaluate these responses to: {prompt}
        
        {comparisons}
        
        Provide:
        1. A combined best answer
        2. Confidence score between 0-1 include upto two decimal points
        3. Brief analysis of differences"""
        
        response = await self.client.chat.completions.create(
            model=arbiter,
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        return {
            "text": content,
            "confidence": self._extract_confidence(content),
            "analysis": self._extract_analysis(content),
            "dissenting_views": self._extract_dissent(content),
        }
        
    def _extract_dissent(self, text: str) -> str:
        # Add your dissent extraction logic here
        return "Dissenting views placeholder"

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from text."""
        # Add your confidence extraction logic here
        return 0.9  # Simplified for example

    def _extract_analysis(self, text: str) -> str:
        """Extract analysis from text."""
        # Add your analysis extraction logic here
        return "Analysis placeholder"