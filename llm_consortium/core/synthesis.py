from typing import List, Dict
from openai import AsyncOpenAI
from ..config.models import LogEntry
from ..utils.prompt_utils import read_arbiter_prompt
from ..utils.extractors import ResponseExtractor

class SynthesisHandler:
    def __init__(self, client: AsyncOpenAI, extractor: ResponseExtractor):
        self.client = client
        self.extractor = extractor

    async def synthesize(self, prompt: str, responses: List[LogEntry], arbiter: str) -> Dict:
        comparisons = "\n\n".join(
            f"Model: {entry.model}\nConfidence: {entry.confidence:.2f}\nResponse:\n{entry.response}"
            for entry in responses
        )
        
        synthesis_prompt = read_arbiter_prompt().format(
            prompt=prompt,
            comparisons=comparisons,
            arbiter=arbiter
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=arbiter,
                messages=[{"role": "user", "content": synthesis_prompt}],
                temperature=0.2
            )
            content = response.choices[0].message.content
            
            return {
                "text": content,
                "confidence": self.extractor.extract_confidence(content),
                "analysis": self._extract_analysis(content),
                "dissenting_views": self._extract_dissent(content),
                "arbiter_model": arbiter
            }
        except Exception as e:
            return {
                "text": f"Error during synthesis: {str(e)}",
                "confidence": 0.0,
                "analysis": "",
                "dissenting_views": "",
                "arbiter_model": arbiter
            }

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