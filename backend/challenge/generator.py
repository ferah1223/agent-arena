"""
AI Challenge Generator for Agent Arena.
Generates fresh challenges using the b.ai API with fallback to question bank.
"""

import json
import os
import uuid
import logging
from typing import Optional

import httpx
from pydantic import BaseModel, Field

from .question_bank import ChallengeQuestion, get_question_bank

logger = logging.getLogger(__name__)

# Configuration from environment
ARENA_AI_API_KEY = os.environ.get("ARENA_AI_API_KEY", "")
ARENA_AI_MODEL = os.environ.get("ARENA_AI_MODEL", "gpt-3.5-turbo")
ARENA_AI_ENDPOINT = "https://api.b.ai/v1/chat/completions"


class GeneratorConfig(BaseModel):
    """Configuration for the AI challenge generator."""
    api_key: str = Field(default_factory=lambda: os.environ.get("ARENA_AI_API_KEY", ""))
    model: str = Field(default_factory=lambda: os.environ.get("ARENA_AI_MODEL", "gpt-3.5-turbo"))
    endpoint: str = ARENA_AI_ENDPOINT
    timeout: float = 30.0
    max_retries: int = 2
    temperature: float = 0.8
    max_tokens: int = 2000


# Prompt templates for each mode
GENERATION_PROMPTS = {
    "debate": """Generate a debate challenge with the following specifications:
Mode: debate
Difficulty: {difficulty}
{custom_topic_line}

Return a JSON object with exactly these fields:
{{
    "title": "A concise, engaging title",
    "description": "One sentence description",
    "content": "The full debate prompt/question that debaters must respond to. Be specific and nuanced.",
    "judge_criteria": ["criterion1", "criterion2", "criterion3", "criterion4", "criterion5"],
    "time_limit": {time_limit}
}}

Make the challenge substantive, thought-provoking, and appropriate for the difficulty level:
- easy: everyday topics, accessible to anyone
- medium: tech/society topics requiring some knowledge
- hard: philosophical/ethical topics requiring deep thinking
- expert: academic/cross-domain topics requiring specialized knowledge

Return ONLY valid JSON, no markdown fences or extra text.""",

    "code_duel": """Generate a coding challenge with the following specifications:
Mode: code_duel
Difficulty: {difficulty}
{custom_topic_line}

Return a JSON object with exactly these fields:
{{
    "title": "Problem title",
    "description": "One sentence description",
    "content": "Full problem statement with examples, constraints, and expected behavior. Include input/output format.",
    "judge_criteria": ["correctness", "time_complexity", "code_quality", "edge_cases"],
    "time_limit": {time_limit},
    "test_cases": [
        {{"input": {{...}}, "expected": ...}},
        {{"input": {{...}}, "expected": ...}},
        {{"input": {{...}}, "expected": ...}}
    ]
}}

Difficulty guidelines:
- easy: array/string basics, simple algorithms
- medium: trees, graphs, dynamic programming
- hard: system design, concurrency, complex algorithms
- expert: compilers, interpreters, database engines, novel algorithms

Return ONLY valid JSON, no markdown fences or extra text.""",

    "ctf": """Generate a Capture The Flag (CTF) cybersecurity challenge:
Mode: ctf
Difficulty: {difficulty}
{custom_topic_line}

Return a JSON object with exactly these fields:
{{
    "title": "Challenge title",
    "description": "One sentence description",
    "content": "Full challenge description including the scenario, what's provided, and what the participant must do. Include hints.",
    "judge_criteria": ["flag_correctness", "technique", "methodology", "documentation"],
    "time_limit": {time_limit},
    "flag_hash": "sha256:placeholder_hash_value"
}}

Difficulty guidelines:
- easy: basic web vulns, encoding, simple crypto
- medium: SQL injection, XSS, SSRF, JWT attacks
- hard: deserialization, race conditions, advanced chains
- expert: full pentest, binary exploitation, custom vuln apps

Return ONLY valid JSON, no markdown fences or extra text.""",

    "research": """Generate a research/writing challenge:
Mode: research
Difficulty: {difficulty}
{custom_topic_line}

Return a JSON object with exactly these fields:
{{
    "title": "Research topic title",
    "description": "One sentence description",
    "content": "Full research prompt specifying what to investigate, cover, and deliver. Be specific about required sections.",
    "judge_criteria": ["accuracy", "depth", "completeness", "sources", "analysis"],
    "time_limit": {time_limit},
    "scoring_rubric": {{
        "dimension1": {{"weight": 0.25, "description": "What this dimension measures"}},
        "dimension2": {{"weight": 0.25, "description": "What this dimension measures"}},
        "dimension3": {{"weight": 0.20, "description": "What this dimension measures"}},
        "dimension4": {{"weight": 0.15, "description": "What this dimension measures"}},
        "dimension5": {{"weight": 0.15, "description": "What this dimension measures"}}
    }}
}}

Difficulty guidelines:
- easy: overviews, introductory guides, basic comparisons
- medium: detailed comparisons, decision frameworks, ethical analyses
- hard: cross-domain analysis, alignment research, comprehensive surveys
- expert: academic-level papers, formal methods, cutting-edge research surveys

Return ONLY valid JSON, no markdown fences or extra text.""",
}

# Time limits by difficulty
DIFFICULTY_TIME_LIMITS = {
    "easy": 300,
    "medium": 420,
    "hard": 600,
    "expert": 900,
}


class ChallengeGenerator:
    """Generates fresh challenges using AI, with fallback to question bank."""

    def __init__(self, config: Optional[GeneratorConfig] = None):
        self.config = config or GeneratorConfig()
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def _build_prompt(
        self,
        mode: str,
        difficulty: str,
        custom_topic: Optional[str] = None,
    ) -> str:
        """Build the generation prompt for the given parameters."""
        template = GENERATION_PROMPTS.get(mode)
        if not template:
            raise ValueError(f"Unknown mode: {mode}")

        custom_topic_line = ""
        if custom_topic:
            custom_topic_line = f"Custom topic/request: {custom_topic}"

        time_limit = DIFFICULTY_TIME_LIMITS.get(difficulty, 600)

        return template.format(
            difficulty=difficulty,
            custom_topic_line=custom_topic_line,
            time_limit=time_limit,
        )

    def _validate_output(self, data: dict, mode: str) -> bool:
        """Validate that the AI output has the required fields."""
        required_fields = ["title", "description", "content", "judge_criteria"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False

        if not isinstance(data["judge_criteria"], list):
            logger.warning("judge_criteria must be a list")
            return False

        if len(data.get("content", "")) < 20:
            logger.warning("Content too short")
            return False

        # Mode-specific validation
        if mode == "code_duel" and "test_cases" not in data:
            logger.warning("code_duel missing test_cases")
            return False

        return True

    async def _call_ai_api(self, prompt: str) -> Optional[dict]:
        """Call the b.ai API to generate a challenge."""
        if not self.config.api_key:
            logger.warning("No API key configured, skipping AI generation")
            return None

        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a challenge designer for an AI competition platform. Generate high-quality, substantive challenges. Return ONLY valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"},
        }

        for attempt in range(self.config.max_retries + 1):
            try:
                response = await client.post(
                    self.config.endpoint,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Parse JSON from response
                # Handle potential markdown fences in response
                content = content.strip()
                if content.startswith("```"):
                    # Remove markdown code fences
                    lines = content.split("\n")
                    content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

                return json.loads(content)

            except httpx.HTTPStatusError as e:
                logger.warning(f"API request failed (attempt {attempt + 1}): {e.response.status_code}")
                if e.response.status_code == 429:
                    # Rate limited, wait and retry
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                break
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.warning(f"Failed to parse API response (attempt {attempt + 1}): {e}")
                continue
            except httpx.RequestError as e:
                logger.warning(f"Request error (attempt {attempt + 1}): {e}")
                break

        return None

    async def generate(
        self,
        mode: str,
        difficulty: str,
        custom_topic: Optional[str] = None,
    ) -> ChallengeQuestion:
        """
        Generate a fresh challenge using AI.

        Args:
            mode: Challenge mode (debate, code_duel, ctf, research)
            difficulty: Difficulty level (easy, medium, hard, expert)
            custom_topic: Optional custom topic/theme

        Returns:
            A ChallengeQuestion, either AI-generated or from the bank

        Raises:
            ValueError: If mode or difficulty is invalid
        """
        valid_modes = ["debate", "code_duel", "ctf", "research"]
        valid_difficulties = ["easy", "medium", "hard", "expert"]

        if mode not in valid_modes:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {valid_modes}")
        if difficulty not in valid_difficulties:
            raise ValueError(f"Invalid difficulty: {difficulty}. Must be one of {valid_difficulties}")

        # Try AI generation
        prompt = self._build_prompt(mode, difficulty, custom_topic)
        ai_output = await self._call_ai_api(prompt)

        if ai_output and self._validate_output(ai_output, mode):
            # Build ChallengeQuestion from AI output
            question_id = f"ai-{mode}-{difficulty}-{uuid.uuid4().hex[:8]}"
            time_limit = ai_output.get("time_limit", DIFFICULTY_TIME_LIMITS[difficulty])

            question_data = {
                "id": question_id,
                "mode": mode,
                "difficulty": difficulty,
                "title": ai_output["title"],
                "description": ai_output["description"],
                "content": ai_output["content"],
                "time_limit": time_limit,
                "judge_criteria": ai_output["judge_criteria"],
            }

            # Add optional fields
            if "test_cases" in ai_output:
                question_data["test_cases"] = ai_output["test_cases"]
            if "flag_hash" in ai_output:
                question_data["flag_hash"] = ai_output["flag_hash"]
            if "scoring_rubric" in ai_output:
                question_data["scoring_rubric"] = ai_output["scoring_rubric"]

            logger.info(f"AI-generated challenge: {question_id}")
            return ChallengeQuestion(**question_data)

        # Fallback to question bank
        logger.info(f"AI generation failed, falling back to question bank for {mode}/{difficulty}")
        bank = get_question_bank()
        question = bank.get_random_question(mode=mode, difficulty=difficulty)

        if question is None:
            # Try without difficulty filter
            question = bank.get_random_question(mode=mode)

        if question is None:
            raise RuntimeError(f"No challenges available in bank for mode={mode}")

        return question

    async def generate_batch(
        self,
        mode: str,
        difficulty: str,
        count: int = 3,
        custom_topic: Optional[str] = None,
    ) -> list[ChallengeQuestion]:
        """Generate multiple unique challenges."""
        import asyncio

        tasks = [
            self.generate(mode, difficulty, custom_topic)
            for _ in range(count)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        questions = []
        seen_ids = set()
        for r in results:
            if isinstance(r, ChallengeQuestion) and r.id not in seen_ids:
                questions.append(r)
                seen_ids.add(r.id)
            elif isinstance(r, Exception):
                logger.warning(f"Batch generation error: {r}")

        return questions
