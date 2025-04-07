# from typing import List, Dict
# from openai import AsyncOpenAI
# from ..config.models import LogEntry
# from ..utils.prompt_utils import read_arbiter_prompt
# from ..utils.extractors import ResponseExtractor
# from typing import List, Dict
# from openai import AsyncOpenAI
# from ..config.models import LogEntry
# from ..utils.prompt_utils import read_arbiter_prompt, read_arbiter_system_prompt
# from ..utils.extractors import ResponseExtractor
# from .synthesis_db import SynthesisDatabaseHandler
# from .spiderlog_db import SpiderDatasetLogger

# from ..utils.logging import logger
# class SynthesisHandler:
#     def __init__(self, client: AsyncOpenAI, extractor: ResponseExtractor):
#         self.client = client
#         self.extractor = extractor
#         self.db_handler = SynthesisDatabaseHandler()
        
#         self.arbiter_system_prompt = read_arbiter_system_prompt()

#     async def synthesize(self, prompt: str, responses: List[LogEntry], 
#                         arbiter: str, iteration: int) -> Dict:
#         comparisons = "\n\n".join(
#             f"Model: {entry.model}\nConfidence: {entry.confidence:.2f}\nResponse:\n{entry.response}"
#             for entry in responses
#         )
        
#         synthesis_prompt = read_arbiter_prompt().format(
#             prompt=prompt,
#             comparisons=comparisons,
#             arbiter=arbiter
#         )
#         #Updated messages with system prompt
#         messages = [{"role": "system", "content": self.arbiter_system_prompt},
#                     {"role": "user", "content": synthesis_prompt}]
#         try:
#             response = await self.client.chat.completions.create(
#                 model=arbiter,
#                 # messages=[{"role": "user", "content": synthesis_prompt}],
#                 messages=messages,
#                 temperature=0.2
#             )
#             content = response.choices[0].message.content
            
#             result = {
#                 "text": content,
#                 "confidence": self.extractor.extract_confidence(content),
#                 "analysis": self._extract_analysis(content),
#                 "dissenting_views": self._extract_dissent(content),
#                 "arbiter_model": arbiter,
#                 "intent": self._extract_intent(content)
#             }

#             # Log to synthesis database FOR QUERY use, log_query
#             self.db_handler.log_synthesis(
#                 iteration=iteration,
#                 prompt=prompt,
#                 arbiter=arbiter,
#                 synthesized_text=result['text'],
#                 confidence=result['confidence'],
#                 analysis=result['analysis'],
#                 dissent=result['dissenting_views'],
#                 intent=result['intent'],
#             )

#             logger.info(
#                 f"Iteration {iteration} Synthesis Complete - "
#                 f"Confidence: {result['confidence']:.2f}"
#             )
            
#             return result
            
#         except Exception as e:
#             error_msg = f"Arbiter synthesis error: {str(e)}"
#             logger.error(error_msg)
#             return {
#                 "text": error_msg,
#                 "confidence": 0.0,
#                 "analysis": "",
#                 "dissenting_views": "",
#                 "arbiter_model": arbiter
#             }    
#     def _extract_analysis(self, text: str) -> str:
#         return self.extractor.extract_section(
#             text, 
#             "### Analysis of Differences:", 
#             "### Dissenting Views:"
#         )

#     def _extract_dissent(self, text: str) -> str:
#         return self.extractor.extract_section(
#             text, 
#             "### Dissenting Views:"
#         )

"""FOR NLQ2SQL TASK"""
from typing import List, Dict
from openai import AsyncOpenAI
from ..config.models import LogEntry
from ..utils.prompt_utils import read_arbiter_prompt, read_arbiter_system_prompt
from ..utils.extractors import ResponseExtractor
from .spiderlog_db import SpiderDatasetLogger
from ..utils.logging import logger
import json

class SynthesisHandler:
    def __init__(self, client: AsyncOpenAI, extractor: ResponseExtractor):
        self.client = client
        self.extractor = extractor
        self.db_handler = SpiderDatasetLogger()
        self.arbiter_system_prompt = read_arbiter_system_prompt()

    async def synthesize(self, prompt: str, responses: List[LogEntry], 
                        arbiter: str, iteration: int) -> Dict:
        comparisons = "\n\n".join(
            f"Model: {entry.model}\nConfidence: {entry.confidence:.2f}\nResponse:\n{entry.response}"
            for entry in responses
        )
        
        synthesis_prompt = read_arbiter_prompt().format(
            prompt=prompt,
            comparisons=comparisons,
            arbiter=arbiter
        )
        
        messages = [
            {"role": "system", "content": self.arbiter_system_prompt},
            {"role": "user", "content": synthesis_prompt}
        ]
        
        try:
            response = await self.client.chat.completions.create(
                model=arbiter,
                messages=messages,
                temperature=0.2
            )
            content = response.choices[0].message.content
            
            result = {
                "text": content,
                "confidence": self.extractor.extract_confidence(content),
                "analysis": self._extract_analysis(content),
                "dissenting_views": self._extract_dissent(content),
                "arbiter_model": arbiter,
                "intent": self._extract_intent(content)
            }

            # Adapt synthesis data to SpiderDatasetLogger's expected format
            self._log_to_spider_db(
                prompt=prompt,
                synthesized_text=result['text'],
                confidence=result['confidence'],
                analysis=result['analysis'],
                dissent=result['dissenting_views'],
                intent=result['intent'],
                model_responses=responses,
                iteration=iteration
            )

            logger.info(
                f"Iteration {iteration} Synthesis Complete - "
                f"Confidence: {result['confidence']:.2f}"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Arbiter synthesis error: {str(e)}"
            logger.error(error_msg)
            return {
                "text": error_msg,
                "confidence": 0.0,
                "analysis": "",
                "dissenting_views": "",
                "arbiter_model": arbiter,
                "intent": ""
            }

    def _log_to_spider_db(self, prompt: str, synthesized_text: str, confidence: float,
                         analysis: str, dissent: str, intent: str, 
                         model_responses: List[LogEntry], iteration: int):
        """Adapter method to map synthesis data to SpiderDatasetLogger format"""
        try:
            # Create a mock database schema for this synthesis entry
            db_schema = f"SynthesisIteration_{iteration}"
            
            # Convert model responses to dict format
            responses_dict = [
                {
                    "model": r.model,
                    "response": r.response,
                    "confidence": r.confidence
                } for r in model_responses
            ]
            
            # Map synthesis data to SpiderDatasetLogger's log_query parameters
            self.db_handler.log_query(
                db_schema=db_schema,
                natural_language_query=prompt,
                intent_category=intent,
                generated_sql=synthesized_text,  # Using synthesized_text as generated_sql
                confidence=confidence,
                model_responses=responses_dict
            )
        except Exception as e:
            logger.error(f"Failed to log synthesis to Spider DB: {str(e)}")
            raise

    def _extract_analysis(self, text: str) -> str:
        return self.extractor.extract_section(
            text, 
            "### Analysis of Differences:", 
            "### Dissenting Views:"
        )

    def _extract_dissent(self, text: str) -> str:
        return self.extractor.extract_section(
            text, 
            "### Dissenting Views:"
        )

    def _extract_intent(self, text: str) -> str:
        return self.extractor.extract_section(
            text,
            "### Intent:"
        )