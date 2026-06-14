"""
Challenge Manager for Agent Arena.
Orchestrates challenge selection from bank and AI generator,
with difficulty mapping and anti-repeat logic.
"""

import time
import uuid
import random
import logging
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from .question_bank import ChallengeQuestion, QuestionBank, get_question_bank
from .generator import ChallengeGenerator, GeneratorConfig

logger = logging.getLogger(__name__)


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class ChallengeMode(str, Enum):
    DEBATE = "debate"
    CODE_DUEL = "code_duel"
    CTF = "ctf"
    RESEARCH = "research"


class ChallengeSource(str, Enum):
    BANK = "bank"
    AI = "ai"
    AUTO = "auto"


class ChallengeTask(BaseModel):
    """A challenge task ready to be presented to participants."""
    task_id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:12]}")
    question: ChallengeQuestion
    source: str  # "bank" or "ai"
    elo_multiplier: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


# Difficulty to Elo multiplier mapping
DIFFICULTY_ELO_MULTIPLIERS = {
    Difficulty.EASY: 1.0,
    Difficulty.MEDIUM: 1.5,
    Difficulty.HARD: 2.0,
    Difficulty.EXPERT: 3.0,
}

# Anti-repeat window: how long to remember recently used challenges
ANTI_REPEAT_WINDOW_HOURS = 24


class ChallengeManager:
    """
    Manages challenge selection, difficulty mapping, and anti-repeat logic.

    The manager coordinates between the question bank and AI generator
    to provide fresh, non-repeating challenges.
    """

    def __init__(
        self,
        generator_config: Optional[GeneratorConfig] = None,
        anti_repeat_hours: float = ANTI_REPEAT_WINDOW_HOURS,
    ):
        self._bank: QuestionBank = get_question_bank()
        self._generator: ChallengeGenerator = ChallengeGenerator(generator_config)
        self._anti_repeat_hours = anti_repeat_hours

        # Track recently used challenges per session
        # Key: session_id, Value: list of (question_id, timestamp)
        self._recent_challenges: dict[str, list[tuple[str, float]]] = {}

        # Global recent history (for session-less lookups)
        self._global_recent: list[tuple[str, float]] = []

    def _cleanup_expired(self, session_id: Optional[str] = None) -> None:
        """Remove expired entries from the anti-repeat tracking."""
        cutoff = time.time() - (self._anti_repeat_hours * 3600)

        # Clean session-specific history
        if session_id and session_id in self._recent_challenges:
            self._recent_challenges[session_id] = [
                (qid, ts) for qid, ts in self._recent_challenges[session_id]
                if ts > cutoff
            ]

        # Clean global history
        self._global_recent = [
            (qid, ts) for qid, ts in self._global_recent
            if ts > cutoff
        ]

    def _get_recent_ids(self, session_id: Optional[str] = None) -> set[str]:
        """Get set of recently used question IDs."""
        self._cleanup_expired(session_id)

        recent_ids = set()

        # Include session-specific history
        if session_id and session_id in self._recent_challenges:
            recent_ids.update(qid for qid, _ in self._recent_challenges[session_id])

        # Also include global recent
        recent_ids.update(qid for qid, _ in self._global_recent)

        return recent_ids

    def _record_usage(
        self,
        question_id: str,
        session_id: Optional[str] = None,
    ) -> None:
        """Record that a question was used."""
        now = time.time()

        if session_id:
            if session_id not in self._recent_challenges:
                self._recent_challenges[session_id] = []
            self._recent_challenges[session_id].append((question_id, now))

        self._global_recent.append((question_id, now))

    def get_elo_multiplier(self, difficulty: str) -> float:
        """
        Get the Elo rating multiplier for a given difficulty level.

        Args:
            difficulty: One of easy, medium, hard, expert

        Returns:
            Elo multiplier (1.0 to 3.0)
        """
        try:
            d = Difficulty(difficulty)
            return DIFFICULTY_ELO_MULTIPLIERS[d]
        except ValueError:
            logger.warning(f"Unknown difficulty '{difficulty}', defaulting to 1.0")
            return 1.0

    async def get_challenge(
        self,
        mode: str,
        difficulty: str = "medium",
        source: str = "auto",
        session_id: Optional[str] = None,
        custom_topic: Optional[str] = None,
    ) -> ChallengeTask:
        """
        Get a challenge task for the given parameters.

        Args:
            mode: Challenge mode (debate, code_duel, ctf, research)
            difficulty: Difficulty level (easy, medium, hard, expert)
            source: Where to get the challenge ('bank', 'ai', or 'auto')
            session_id: Optional session ID for anti-repeat tracking
            custom_topic: Optional custom topic for AI generation

        Returns:
            ChallengeTask with the selected challenge

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If no challenge can be obtained
        """
        # Validate inputs
        valid_modes = [m.value for m in ChallengeMode]
        valid_difficulties = [d.value for d in Difficulty]

        if mode not in valid_modes:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {valid_modes}")
        if difficulty not in valid_difficulties:
            raise ValueError(f"Invalid difficulty: {difficulty}. Must be one of {valid_difficulties}")

        recent_ids = self._get_recent_ids(session_id)
        elo_multiplier = self.get_elo_multiplier(difficulty)

        question = None
        actual_source = None

        if source == "bank" or source == "auto":
            # Try bank first (for both 'bank' and 'auto')
            question = self._bank.get_random_question(
                mode=mode,
                difficulty=difficulty,
                exclude_ids=recent_ids,
            )
            if question:
                actual_source = "bank"

            # If bank exhausted within anti-repeat window, try without exclusion
            if question is None and source == "bank":
                question = self._bank.get_random_question(
                    mode=mode,
                    difficulty=difficulty,
                )
                if question:
                    actual_source = "bank"
                    logger.info("Anti-repeat window exhausted, allowing repeat from bank")

        if question is None and (source == "ai" or source == "auto"):
            # Try AI generation
            try:
                question = await self._generator.generate(
                    mode=mode,
                    difficulty=difficulty,
                    custom_topic=custom_topic,
                )
                actual_source = "ai" if question.id.startswith("ai-") else "bank"
            except Exception as e:
                logger.error(f"AI generation failed: {e}")
                # For 'ai' source, try bank as last resort
                if source == "ai":
                    question = self._bank.get_random_question(
                        mode=mode,
                        difficulty=difficulty,
                        exclude_ids=recent_ids,
                    )
                    if question:
                        actual_source = "bank"

        if question is None:
            raise RuntimeError(
                f"Could not obtain challenge for mode={mode}, difficulty={difficulty}, source={source}"
            )

        # Record usage for anti-repeat
        self._record_usage(question.id, session_id)

        # Create the task
        task = ChallengeTask(
            question=question,
            source=actual_source or "unknown",
            elo_multiplier=elo_multiplier,
            session_id=session_id,
        )

        logger.info(
            f"Challenge selected: {task.task_id} | "
            f"question={question.id} | source={actual_source} | "
            f"mode={mode} | difficulty={difficulty} | elo_mult={elo_multiplier}"
        )

        return task

    def get_stats(self) -> dict:
        """Get statistics about the challenge manager state."""
        bank = self._bank
        return {
            "bank_counts": {
                mode: bank.get_question_count(mode=mode)
                for mode in bank.get_available_modes()
            },
            "total_bank_questions": sum(
                bank.get_question_count(mode=m)
                for m in bank.get_available_modes()
            ),
            "recent_challenge_count": len(self._global_recent),
            "active_sessions": len(self._recent_challenges),
            "elo_multipliers": {
                d.value: DIFFICULTY_ELO_MULTIPLIERS[d]
                for d in Difficulty
            },
            "anti_repeat_window_hours": self._anti_repeat_hours,
        }

    def clear_session(self, session_id: str) -> None:
        """Clear anti-repeat history for a session."""
        self._recent_challenges.pop(session_id, None)

    def clear_all_sessions(self) -> None:
        """Clear all anti-repeat history."""
        self._recent_challenges.clear()
        self._global_recent.clear()

    async def close(self) -> None:
        """Clean up resources."""
        await self._generator.close()


# Singleton instance
_manager: Optional[ChallengeManager] = None


def get_challenge_manager(
    generator_config: Optional[GeneratorConfig] = None,
) -> ChallengeManager:
    """Get the singleton ChallengeManager instance."""
    global _manager
    if _manager is None:
        _manager = ChallengeManager(generator_config=generator_config)
    return _manager
