#!/usr/bin/env python3
"""AI Quality Evaluation Script for Thesis.

This script evaluates the quality of Thesis's AI responses by comparing:
1. Responses WITH RAG context (using user documents)
2. Responses WITHOUT RAG context (generic responses)

It uses an LLM-as-judge approach to score responses on multiple dimensions.

Usage:
    cd backend
    source venv/bin/activate
    python run_quality_evaluation.py

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - VOYAGE_API_KEY environment variable set (for RAG)
    - Supabase connection configured
"""

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Configuration
# ============================================================================


@dataclass
class EvaluationConfig:
    """Configuration for quality evaluation."""

    num_test_questions: int = 10
    judge_model: str = "claude-sonnet-4-20250514"
    response_model: str = "claude-sonnet-4-20250514"
    output_file: str = "quality_evaluation_results.json"


# ============================================================================
# Test Questions
# ============================================================================

TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "How do I design an effective onboarding program for new sales representatives?",
        "category": "instructional_design",
        "expected_context": "sales training, onboarding best practices",
    },
    {
        "id": 2,
        "question": "What are the key principles of adult learning I should apply to my leadership development curriculum?",
        "category": "learning_theory",
        "expected_context": "adult learning theory, andragogy",
    },
    {
        "id": 3,
        "question": "Can you help me create learning objectives for a compliance training module?",
        "category": "learning_objectives",
        "expected_context": "Bloom's taxonomy, measurable objectives",
    },
    {
        "id": 4,
        "question": "How should I measure the ROI of our training programs?",
        "category": "measurement",
        "expected_context": "Kirkpatrick model, Phillips ROI",
    },
    {
        "id": 5,
        "question": "What engagement techniques work best for virtual instructor-led training?",
        "category": "facilitation",
        "expected_context": "virtual facilitation, engagement strategies",
    },
    {
        "id": 6,
        "question": "How do I create a facilitator guide for a workshop?",
        "category": "materials_development",
        "expected_context": "facilitator guides, training materials",
    },
    {
        "id": 7,
        "question": "What are best practices for designing scenario-based learning?",
        "category": "instructional_design",
        "expected_context": "scenario-based learning, simulations",
    },
    {
        "id": 8,
        "question": "How can I incorporate spaced repetition into our training programs?",
        "category": "learning_science",
        "expected_context": "spaced repetition, memory, retention",
    },
    {
        "id": 9,
        "question": "What should I include in a needs analysis for a technical skills training?",
        "category": "analysis",
        "expected_context": "needs analysis, skills gap analysis",
    },
    {
        "id": 10,
        "question": "How do I design microlearning modules that actually drive behavior change?",
        "category": "microlearning",
        "expected_context": "microlearning, behavior change, nudge theory",
    },
]


# ============================================================================
# Evaluation Criteria
# ============================================================================

EVALUATION_RUBRIC = """
You are evaluating the quality of an L&D (Learning & Development) AI assistant's response.

Score each dimension from 1-5:

1. SPECIFICITY (1-5):
   1 = Generic advice that could apply to any situation
   2 = Somewhat specific but missing key details
   3 = Moderately specific with some concrete examples
   4 = Specific with clear examples and frameworks
   5 = Highly specific with detailed, actionable guidance

2. RELEVANCE (1-5):
   1 = Does not address the question
   2 = Partially addresses the question
   3 = Addresses the core question
   4 = Fully addresses the question with additional context
   5 = Perfectly addresses the question with insightful depth

3. PERSONALIZATION (1-5):
   1 = No use of available context
   2 = Minimal reference to context
   3 = Some integration of context
   4 = Good use of context to tailor response
   5 = Excellent personalization using all available context

4. ACCURACY (1-5):
   1 = Contains significant errors
   2 = Some inaccuracies present
   3 = Generally accurate
   4 = Accurate with minor caveats
   5 = Completely accurate and well-grounded

5. ACTIONABILITY (1-5):
   1 = No clear next steps
   2 = Vague suggestions
   3 = Some actionable items
   4 = Clear action items with guidance
   5 = Comprehensive action plan with resources

Return your evaluation as JSON:
{
    "specificity": <1-5>,
    "relevance": <1-5>,
    "personalization": <1-5>,
    "accuracy": <1-5>,
    "actionability": <1-5>,
    "overall_score": <average of above>,
    "strengths": "<brief summary of strengths>",
    "weaknesses": "<brief summary of weaknesses>",
    "improvement_suggestions": "<specific suggestions>"
}
"""


# ============================================================================
# Evaluation Results
# ============================================================================


@dataclass
class EvaluationResult:
    """Result of evaluating a single response."""

    question_id: int
    question: str
    category: str
    with_context: bool
    response: str
    scores: Dict[str, float]
    strengths: str
    weaknesses: str
    improvement_suggestions: str


@dataclass
class EvaluationSummary:
    """Summary of all evaluation results."""

    timestamp: str
    total_questions: int
    with_context_avg: Dict[str, float]
    without_context_avg: Dict[str, float]
    improvement_percentage: Dict[str, float]
    overall_improvement: float


# ============================================================================
# Evaluation Functions
# ============================================================================


async def get_response_with_rag(question: str, client) -> str:
    """Get a response using RAG context."""
    try:
        # Import the chat logic
        from document_processor import search_similar_chunks

        # Search for relevant context
        context_chunks = search_similar_chunks(
            query=question,
            client_id="00000000-0000-0000-0000-000000000001",  # Default client
            limit=5,
        )

        # Build context string
        context = "\n\n".join(
            [
                f"[Document Context {i + 1}]: {chunk.get('content', '')}"
                for i, chunk in enumerate(context_chunks)
            ]
        )

        # Get response with context
        system_prompt = """You are Thesis, an AI assistant specialized in Learning & Development.
        Use the following context from the user's documents to provide a personalized response:

        {context}

        If the context is relevant, reference it in your response. If not, provide your expert guidance.
        """

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt.format(
                context=context if context else "No specific context available."
            ),
            messages=[{"role": "user", "content": question}],
        )

        return message.content[0].text

    except Exception as e:
        return f"Error generating response with RAG: {str(e)}"


async def get_response_without_rag(question: str, client) -> str:
    """Get a response without RAG context."""
    try:
        system_prompt = """You are Thesis, an AI assistant specialized in Learning & Development.
        Provide expert guidance on instructional design, training development, and learning science."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        )

        return message.content[0].text

    except Exception as e:
        return f"Error generating response without RAG: {str(e)}"


async def evaluate_response(question: str, response: str, with_context: bool, judge_client) -> Dict:
    """Use LLM-as-judge to evaluate a response."""
    try:
        evaluation_prompt = f"""
{EVALUATION_RUBRIC}

Question asked: "{question}"

Response to evaluate:
\"\"\"
{response}
\"\"\"

Context available: {"Yes - user's documents were searched" if with_context else "No - generic response only"}

Provide your JSON evaluation:
"""

        message = judge_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": evaluation_prompt}],
        )

        # Parse JSON from response
        response_text = message.content[0].text
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0]
        else:
            json_str = response_text

        return json.loads(json_str.strip())

    except Exception as e:
        return {
            "specificity": 0,
            "relevance": 0,
            "personalization": 0,
            "accuracy": 0,
            "actionability": 0,
            "overall_score": 0,
            "strengths": "Error during evaluation",
            "weaknesses": str(e),
            "improvement_suggestions": "Fix evaluation error",
        }


def calculate_summary(results: List[EvaluationResult]) -> EvaluationSummary:
    """Calculate summary statistics from evaluation results."""
    with_context = [r for r in results if r.with_context]
    without_context = [r for r in results if not r.with_context]

    def avg_scores(evals: List[EvaluationResult]) -> Dict[str, float]:
        if not evals:
            return {}
        dimensions = [
            "specificity",
            "relevance",
            "personalization",
            "accuracy",
            "actionability",
            "overall_score",
        ]
        return {dim: sum(e.scores.get(dim, 0) for e in evals) / len(evals) for dim in dimensions}

    with_avg = avg_scores(with_context)
    without_avg = avg_scores(without_context)

    improvement = {}
    for dim in with_avg:
        if without_avg.get(dim, 0) > 0:
            improvement[dim] = ((with_avg[dim] - without_avg[dim]) / without_avg[dim]) * 100
        else:
            improvement[dim] = 0

    return EvaluationSummary(
        timestamp=datetime.now().isoformat(),
        total_questions=len(TEST_QUESTIONS),
        with_context_avg=with_avg,
        without_context_avg=without_avg,
        improvement_percentage=improvement,
        overall_improvement=improvement.get("overall_score", 0),
    )


# ============================================================================
# Main Evaluation Runner
# ============================================================================


async def run_evaluation():
    """Run the complete quality evaluation."""
    print("=" * 60)
    print("Thesis AI Quality Evaluation")
    print("=" * 60)
    print()

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it in your .env file or environment")
        return

    # Initialize client
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
    except ImportError:
        print("ERROR: anthropic package not installed")
        print("Run: pip install anthropic")
        return

    config = EvaluationConfig()
    results: List[EvaluationResult] = []

    print(f"Running {len(TEST_QUESTIONS)} test questions...")
    print("Comparing WITH vs WITHOUT RAG context")
    print()

    for i, test in enumerate(TEST_QUESTIONS[: config.num_test_questions]):
        print(f"[{i + 1}/{config.num_test_questions}] Evaluating: {test['question'][:50]}...")

        # Get response WITHOUT context
        response_no_context = await get_response_without_rag(test["question"], client)
        eval_no_context = await evaluate_response(
            test["question"], response_no_context, False, client
        )

        results.append(
            EvaluationResult(
                question_id=test["id"],
                question=test["question"],
                category=test["category"],
                with_context=False,
                response=response_no_context,
                scores=eval_no_context,
                strengths=eval_no_context.get("strengths", ""),
                weaknesses=eval_no_context.get("weaknesses", ""),
                improvement_suggestions=eval_no_context.get("improvement_suggestions", ""),
            )
        )

        # Get response WITH context
        response_with_context = await get_response_with_rag(test["question"], client)
        eval_with_context = await evaluate_response(
            test["question"], response_with_context, True, client
        )

        results.append(
            EvaluationResult(
                question_id=test["id"],
                question=test["question"],
                category=test["category"],
                with_context=True,
                response=response_with_context,
                scores=eval_with_context,
                strengths=eval_with_context.get("strengths", ""),
                weaknesses=eval_with_context.get("weaknesses", ""),
                improvement_suggestions=eval_with_context.get("improvement_suggestions", ""),
            )
        )

        print(f"  Without Context: {eval_no_context.get('overall_score', 0):.1f}/5")
        print(f"  With Context:    {eval_with_context.get('overall_score', 0):.1f}/5")
        print()

    # Calculate summary
    summary = calculate_summary(results)

    # Print summary
    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print()
    print("Average Scores by Dimension:")
    print("-" * 40)
    print(f"{'Dimension':<20} {'No Context':>12} {'With Context':>12} {'Improvement':>12}")
    print("-" * 40)

    dimensions = [
        "specificity",
        "relevance",
        "personalization",
        "accuracy",
        "actionability",
        "overall_score",
    ]
    for dim in dimensions:
        no_ctx = summary.without_context_avg.get(dim, 0)
        with_ctx = summary.with_context_avg.get(dim, 0)
        improve = summary.improvement_percentage.get(dim, 0)
        print(f"{dim:<20} {no_ctx:>12.2f} {with_ctx:>12.2f} {improve:>11.1f}%")

    print("-" * 40)
    print()
    print(f"OVERALL IMPROVEMENT: {summary.overall_improvement:.1f}%")
    print()

    # Save results
    output = {"summary": asdict(summary), "results": [asdict(r) for r in results]}

    with open(config.output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: {config.output_file}")
    print()

    # Recommendations
    print("=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    if summary.overall_improvement > 20:
        print(
            "✅ RAG is providing significant value (+{:.1f}%)".format(summary.overall_improvement)
        )
    elif summary.overall_improvement > 10:
        print("📊 RAG is providing moderate value (+{:.1f}%)".format(summary.overall_improvement))
    else:
        print("⚠️  RAG impact is minimal (+{:.1f}%)".format(summary.overall_improvement))
        print("   Consider improving document quality or embedding strategy")

    print()
    print("Dimension-specific insights:")
    for dim in dimensions[:-1]:  # Exclude overall_score
        improve = summary.improvement_percentage.get(dim, 0)
        if improve < 5:
            print(f"  - {dim}: Consider improving (only +{improve:.1f}% with context)")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    print()
    print("Starting Thesis Quality Evaluation...")
    print()

    # Run evaluation
    asyncio.run(run_evaluation())
