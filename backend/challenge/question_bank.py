"""
Question Bank for Agent Arena Challenge System.
Loads and manages pre-built challenge questions from JSON data files.
"""

import json
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


DATA_DIR = Path(__file__).parent / "data"


class ChallengeQuestion(BaseModel):
    """Represents a single challenge question from the question bank."""
    id: str
    mode: str  # debate, code_duel, ctf, research
    difficulty: str  # easy, medium, hard, expert
    title: str
    description: str
    content: str
    time_limit: int = 600  # seconds
    judge_criteria: list[str] = Field(default_factory=list)
    # Optional fields depending on mode
    test_cases: Optional[list[dict]] = None  # For code_duel
    flag_hash: Optional[str] = None  # For CTF
    scoring_rubric: Optional[dict] = None  # For research

    class Config:
        json_schema_extra = {
            "example": {
                "id": "debate-easy-001",
                "mode": "debate",
                "difficulty": "easy",
                "title": "Cats vs Dogs",
                "description": "Debate pets",
                "content": "Argue for cats or dogs...",
                "time_limit": 300,
                "judge_criteria": ["persuasiveness"]
            }
        }


class QuestionBank:
    """Manages loading and querying of pre-built challenge questions."""

    def __init__(self):
        self._questions: dict[str, list[ChallengeQuestion]] = {
            "debate": [],
            "code_duel": [],
            "ctf": [],
            "research": [],
        }
        self._by_id: dict[str, ChallengeQuestion] = {}
        self._loaded = False

    def load_all(self) -> None:
        """Load all question bank JSON files."""
        if self._loaded:
            return

        files = {
            "debate": "debate.json",
            "code_duel": "code_duel.json",
            "ctf": "ctf.json",
            "research": "research.json",
        }

        for mode, filename in files.items():
            filepath = DATA_DIR / filename
            if filepath.exists():
                with open(filepath, "r") as f:
                    raw_questions = json.load(f)
                    for q_data in raw_questions:
                        question = ChallengeQuestion(**q_data)
                        self._questions[mode].append(question)
                        self._by_id[question.id] = question

        self._loaded = True

    def get_question(self, question_id: str) -> Optional[ChallengeQuestion]:
        """Get a specific question by ID."""
        if not self._loaded:
            self.load_all()
        return self._by_id.get(question_id)

    def get_questions(
        self,
        mode: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> list[ChallengeQuestion]:
        """
        Get questions filtered by mode and/or difficulty.

        Args:
            mode: Filter by challenge mode (debate, code_duel, ctf, research)
            difficulty: Filter by difficulty level (easy, medium, hard, expert)

        Returns:
            List of matching ChallengeQuestion objects
        """
        if not self._loaded:
            self.load_all()

        if mode and mode not in self._questions:
            return []

        results = []
        modes = [mode] if mode else list(self._questions.keys())

        for m in modes:
            for q in self._questions[m]:
                if difficulty is None or q.difficulty == difficulty:
                    results.append(q)

        return results

    def get_random_question(
        self,
        mode: str,
        difficulty: Optional[str] = None,
        exclude_ids: Optional[set[str]] = None,
    ) -> Optional[ChallengeQuestion]:
        """
        Get a random question matching criteria, excluding specified IDs.

        Args:
            mode: Challenge mode
            difficulty: Optional difficulty filter
            exclude_ids: Set of question IDs to exclude (for anti-repeat)

        Returns:
            A random matching question, or None if no matches
        """
        import random

        candidates = self.get_questions(mode=mode, difficulty=difficulty)
        if exclude_ids:
            candidates = [q for q in candidates if q.id not in exclude_ids]

        if not candidates:
            return None

        return random.choice(candidates)

    def get_question_count(
        self,
        mode: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> int:
        """Get the count of questions matching the given filters."""
        return len(self.get_questions(mode=mode, difficulty=difficulty))

    def get_available_modes(self) -> list[str]:
        """Get list of available challenge modes."""
        if not self._loaded:
            self.load_all()
        return [m for m, qs in self._questions.items() if qs]

    def get_available_difficulties(self, mode: Optional[str] = None) -> list[str]:
        """Get list of available difficulty levels, optionally filtered by mode."""
        if not self._loaded:
            self.load_all()

        difficulties = set()
        modes = [mode] if mode else list(self._questions.keys())

        for m in modes:
            for q in self._questions[m]:
                difficulties.add(q.difficulty)

        # Return in order
        order = ["easy", "medium", "hard", "expert"]
        return [d for d in order if d in difficulties]

    def add_question(self, question: ChallengeQuestion) -> None:
        """Dynamically add a question to the bank (e.g., from AI generator)."""
        if question.mode not in self._questions:
            self._questions[question.mode] = []
        self._questions[question.mode].append(question)
        self._by_id[question.id] = question

    def reload(self) -> None:
        """Force reload all question banks from disk."""
        self._loaded = False
        self._questions = {m: [] for m in self._questions}
        self._by_id.clear()
        self.load_all()


# Singleton instance
_question_bank: Optional[QuestionBank] = None


def get_question_bank() -> QuestionBank:
    """Get the singleton QuestionBank instance."""
    global _question_bank
    if _question_bank is None:
        _question_bank = QuestionBank()
        _question_bank.load_all()
    return _question_bank
