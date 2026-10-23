"""Category and question lookup tools for Open Trivia DB."""

import html
from typing import Literal

from helpers.trivia_api import get_trivia_data


class TriviaTools:
    def get_categories(self) -> str:
        """Get all available trivia categories with their IDs."""
        data = get_trivia_data("api_category.php")
        return "\n".join(
            f"{cat['id']}: {html.unescape(cat['name'])}"
            for cat in data["trivia_categories"]
        )

    def get_questions(
        self, amount: int, category: int, difficulty: Literal["easy", "medium", "hard"]
    ) -> str:
        """Fetch multiple-choice trivia questions and their answers.

        Args:
            amount: Number of questions (1-10).
            category: Category ID (use get_categories to see options).
            difficulty: easy, medium, or hard.
        """
        if not 1 <= amount <= 10:
            raise ValueError("amount must be between 1 and 10")
        if difficulty not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty must be easy, medium, or hard")
        data = get_trivia_data(
            "api.php",
            {"amount": amount, "category": category, "difficulty": difficulty, "type": "multiple"},
        )
        lines = []
        for i, question in enumerate(data["results"], 1):
            correct = html.unescape(question["correct_answer"])
            wrong = [html.unescape(answer) for answer in question["incorrect_answers"]]
            lines.append(f"Question {i}: {html.unescape(question['question'])}")
            lines.append(f"  Correct answer: {correct}")
            lines.append(f"  Wrong answers: {', '.join(wrong)}")
            lines.append("")
        return "\n".join(lines)
