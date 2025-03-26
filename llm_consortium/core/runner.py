# import asyncio
# import os
# from datetime import datetime
# from typing import List, Dict
# from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
# from openai import AsyncOpenAI
# from ..config.models import ConsortiumConfig, LogEntry
# from .database import DatabaseHandler
# from .synthesis import SynthesisHandler
# from ..utils.extractors import ResponseExtractor
# from ..utils.prompt_utils import read_iteration_prompt , read_system_prompt
# from dotenv import load_dotenv
# from .logging import logger
# from .synthesis_db import SynthesisDatabaseHandler
# load_dotenv()
# class ConsortiumRunner:
#     def __init__(self):
#         self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#         self.db_handler = DatabaseHandler()
#         self.extractor = ResponseExtractor()
#         ################################################################
#         self.synthesis_db_handler = SynthesisDatabaseHandler()
#         ################################################################
#         self.synthesis_handler = SynthesisHandler(self.client, self.extractor)
#         self.index = VectorStoreIndex.from_documents(
#             SimpleDirectoryReader("data").load_data()
#         )
#         self.system_prompt=read_system_prompt()
#         self.iteration_prompt_template = read_iteration_prompt()

#     async def _query_model(self, model: str, prompt: str, instance: int, iteration: int) -> LogEntry:
#         """Query a single model instance"""
#         start_time = datetime.now()
#         try:
#             query_engine = self.index.as_query_engine()
#             context = str(query_engine.query(prompt))
#             model_prompt = self.iteration_prompt_template.format(
#                 context=context,
#                 prompt=prompt,
#                 model=model
#             )
#             messages = [
#                 {"role": "system", "content": self.system_prompt},
#                 {"role": "user", "content": model_prompt}
#             ]
#             response = await self.client.chat.completions.create(
#                 model=model,
#                 messages=messages,
#                 temperature=0.2
#             )
#             content = response.choices[0].message.content
            
#             return LogEntry(
#                 prompt=prompt,
#                 model=f"{model}-{instance}",
#                 response=self.extractor.extract_answer(content),
#                 confidence=self.extractor.extract_confidence(content),
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

#     async def run_consortium(self, config: ConsortiumConfig, prompt: str) -> Dict:
#         responses = []
#         final_result = None

#         try:
#             #################################################################
#             for iteration in range(config.max_iterations):
#                 logger.info(f"Starting iteration {iteration + 1} of {config.max_iterations}")
#             ###############################################################    
#             for iteration in range(config.max_iterations):
#                 tasks = [
#                     self._query_model(model, prompt, instance, iteration)
#                     for model, count in config.models.items()
#                     for instance in range(count)
#                 ]

#                 results = await asyncio.gather(*tasks, return_exceptions=True)

#                 for result in results:
#                     if isinstance(result, Exception):
#                         continue
#                     self.db_handler.log_interaction(result)
#                     responses.append(result.to_dict())
#                 synthesis = await self.synthesis_handler.synthesize(
#                     prompt, 
#                     [r for r in results if not isinstance(r, Exception)],
#                     config.arbiter,
#                     ################################################
#                     iteration + 1  # Pass current iteration number
#                 )
#                 logger.info(
#                     f"Iteration {iteration + 1} - "
#                     f"Confidence Score: {synthesis['confidence']:.2f}/"
#                     f"{config.confidence_threshold}"
#                 )
#                 #################################################3
#                 final_result = {
#                     "synthesis": synthesis,
#                     "raw_responses": responses,
#                     "iterations": iteration + 1
#                 }

#                 if (synthesis['confidence'] >= config.confidence_threshold and
#                     iteration >= config.min_iterations - 1):
#                     break

#         finally:
#             self.db_handler.close()
#             self.synthesis_db_handler.close()
#         return final_result
import asyncio
import os
from datetime import datetime
from typing import List, Dict
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from openai import AsyncOpenAI
from ..config.models import ConsortiumConfig, LogEntry
from .database import DatabaseHandler
from .synthesis import SynthesisHandler
from ..utils.extractors import ResponseExtractor
from ..utils.prompt_utils import read_iteration_prompt , read_system_prompt
from dotenv import load_dotenv
from .logging import logger
from .synthesis_db import SynthesisDatabaseHandler
from .rag import RAGHandler
load_dotenv()
class ConsortiumRunner:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db_handler = DatabaseHandler()
        self.extractor = ResponseExtractor()
        ################################################################
        self.synthesis_db_handler = SynthesisDatabaseHandler()
        ################################################################
        self.synthesis_handler = SynthesisHandler(self.client, self.extractor)
        # self.index = VectorStoreIndex.from_documents(
        #     SimpleDirectoryReader("data").load_data()
        # )
        self.system_prompt=read_system_prompt()
        self.iteration_prompt_template = read_iteration_prompt()
        self.rag_handler = RAGHandler()
 
 
    async def _query_model(self, model: str, prompt: str, instance: int, iteration: int) -> LogEntry:
        """Query a single model instance"""
        start_time = datetime.now()
        try:
            context = self.rag_handler.get_context(prompt)
            # query_engine = self.index.as_query_engine()
            # context = str(query_engine.query(prompt))
            model_prompt = self.iteration_prompt_template.format(
                context=context,
                prompt=prompt,
                model=model
            )
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": model_prompt}
            ]
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2
            )
            content = response.choices[0].message.content
           
            return LogEntry(
                prompt=prompt,
                model=f"{model}-{instance}",
                response=self.extractor.extract_answer(content),
                confidence=self.extractor.extract_confidence(content),
                latency=(datetime.now() - start_time).total_seconds(),
                iteration=iteration
            )
        except Exception as e:
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
            #################################################################
            for iteration in range(config.max_iterations):
                logger.info(f"Starting iteration {iteration + 1} of {config.max_iterations}")
            ###############################################################    
            for iteration in range(config.max_iterations):
                tasks = [
                    self._query_model(model, prompt, instance, iteration)
                    for model, count in config.models.items()
                    for instance in range(count)
                ]
 
                results = await asyncio.gather(*tasks, return_exceptions=True)
 
                for result in results:
                    if isinstance(result, Exception):
                        continue
                    self.db_handler.log_interaction(result)
                    responses.append(result.to_dict())
                synthesis = await self.synthesis_handler.synthesize(
                    prompt,
                    [r for r in results if not isinstance(r, Exception)],
                    config.arbiter,
                    ################################################
                    iteration + 1  # Pass current iteration number
                )
                logger.info(
                    f"Iteration {iteration + 1} - "
                    f"Confidence Score: {synthesis['confidence']:.2f}/"
                    f"{config.confidence_threshold}"
                )
                #################################################3
                final_result = {
                    "synthesis": synthesis,
                    "raw_responses": responses,
                    "iterations": iteration + 1
                }
 
                if (synthesis['confidence'] >= config.confidence_threshold and
                    iteration >= config.min_iterations - 1):
                    break
 
        finally:
            self.db_handler.close()
            self.synthesis_db_handler.close()
        return final_result