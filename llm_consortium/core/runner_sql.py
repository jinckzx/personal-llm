import asyncio
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from openai import AsyncOpenAI
from ..config.models import ConsortiumConfig, LogEntry
from .database import DatabaseHandler
from .synthesis import SynthesisHandler
from ..utils.extractors import ResponseExtractor
from ..utils.prompt_utils import read_iteration_prompt_sql, read_system_prompt
from dotenv import load_dotenv
from ..utils.logging import logger
from .synthesis_db import SynthesisDatabaseHandler
from .rag import RAGHandler

load_dotenv()

SCHEMA_PATH = "D:\\inforigin_projects\\personal-llm\\dataset\\spider_data\\database\\{db_id}\\schema.sql"

class ConsortiumRunnerSQL:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.db_handler = DatabaseHandler()
        self.extractor = ResponseExtractor()
        self.synthesis_db_handler = SynthesisDatabaseHandler()
        self.synthesis_handler = SynthesisHandler(self.client, self.extractor)
        self.system_prompt = read_system_prompt()
        self.iteration_prompt_template = read_iteration_prompt_sql()
        self.rag_handler = RAGHandler()

    def ingest_csv(self, csv_path: str) -> List[Dict[str, str]]:
        """Load user-provided CSV file containing 'db_id' and 'question'."""
        df = pd.read_csv(csv_path)
        if "db_id" not in df.columns or "question" not in df.columns:
            raise ValueError("CSV must contain 'db_id' and 'question' columns.")
        return df.to_dict(orient="records")

    def get_schema(self, db_id: str) -> str:
        """Fetch the schema for the given db_id from the corresponding SQL file."""
        schema_file = SCHEMA_PATH.format(db_id=db_id)
        if not os.path.exists(schema_file):
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        with open(schema_file, "r") as f:
            return f.read()

    async def _query_model(self, model: str, prompt: str, instance: int, iteration: int, db_id: str) -> LogEntry:
        """Query a single model instance"""
        start_time = datetime.now()
        try:
            context = self.get_schema(db_id)
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
                iteration=iteration,
                intent= self.extractor.extract_intent(content),
                db_id=db_id
            )
        except Exception as e:
            return LogEntry(
                prompt=prompt,
                model=f"{model}-{instance}",
                response=str(e),
                confidence=0.0,
                latency=(datetime.now() - start_time).total_seconds(),
                iteration=iteration,
                intent="",  # Empty intent in case of failure
                db_id=db_id
            )

    async def run_consortium(self, config: ConsortiumConfig, csv_path: str) -> List[Dict]:
        responses = []
        final_results = []
        queries = self.ingest_csv(csv_path)

        try:
            for query in queries:
                db_id = query["db_id"]
                prompt = query["question"]
                
                for iteration in range(config.max_iterations):
                    logger.info(f"Starting iteration {iteration + 1} of {config.max_iterations} for DB: {db_id}")
                    tasks = [
                        self._query_model(model, prompt, instance, iteration, db_id)
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
                        iteration + 1
                    )
                    intents = [r.intent for r in results if not isinstance(r, Exception)]
                    dominant_intent = max(set(intents), key=intents.count) if intents else "unknown"
                    logger.info(
                        f"Iteration {iteration + 1} - "
                        f"Confidence Score: {synthesis['confidence']:.2f}/"
                        f"{config.confidence_threshold}"
                    
                    )
                    
                    final_result = {
                        "synthesis": synthesis,
                        "raw_responses": responses,
                        "iterations": iteration + 1,
                        "intent": dominant_intent,
                        "db_id": db_id
                    }
                    
                    final_results.append(final_result)
                    
                    if (synthesis['confidence'] >= config.confidence_threshold and
                        iteration >= config.min_iterations - 1):
                        break

        finally:
            self.db_handler.close()
            self.synthesis_db_handler.close()
        return final_results
