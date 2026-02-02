#!/usr/bin/env python3
"""Analyze Help System Gaps

This script queries the database to analyze:
1. Low confidence responses (similarity < 0.75)
2. All user questions from help conversations
3. Patterns in what users are asking vs what documentation covers

Run from backend directory:
    python scripts/analyze_help_gaps.py
"""

import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database import get_supabase

supabase = get_supabase()


def analyze_help_data(days: int = 90):
    """Analyze help conversations and identify documentation gaps."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    print(f"\n{'=' * 60}")
    print("HELP SYSTEM GAP ANALYSIS")
    print(
        f"Period: Last {days} days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
    )
    print(f"{'=' * 60}\n")

    # Get all help messages
    messages_result = (
        supabase.table("help_messages")
        .select("id, conversation_id, role, content, sources, feedback, timestamp")
        .gte("timestamp", start_date.isoformat())
        .order("timestamp", desc=True)
        .execute()
    )

    messages = messages_result.data or []
    print(f"Total messages found: {len(messages)}")

    # Get conversations for context
    conversations_result = (
        supabase.table("help_conversations")
        .select("id, user_id, title, created_at, help_type")
        .gte("created_at", start_date.isoformat())
        .execute()
    )

    conversations = {c["id"]: c for c in (conversations_result.data or [])}
    print(f"Total conversations: {len(conversations)}")

    # Analyze messages
    user_questions = []
    low_confidence_responses = []
    all_responses = []

    for msg in messages:
        if msg.get("role") == "user":
            conv = conversations.get(msg["conversation_id"], {})
            user_questions.append(
                {
                    "question": msg.get("content", ""),
                    "help_type": conv.get("help_type", "user"),
                    "timestamp": msg.get("timestamp"),
                }
            )
        elif msg.get("role") == "assistant":
            sources = msg.get("sources") or []
            conv = conversations.get(msg["conversation_id"], {})

            if sources:
                similarities = [s.get("similarity", 0) for s in sources if s.get("similarity")]
                if similarities:
                    avg_similarity = sum(similarities) / len(similarities)

                    response_data = {
                        "response": msg.get("content", ""),
                        "avg_similarity": avg_similarity,
                        "sources": sources,
                        "help_type": conv.get("help_type", "user"),
                        "timestamp": msg.get("timestamp"),
                        "feedback": msg.get("feedback"),
                    }
                    all_responses.append(response_data)

                    if avg_similarity < 0.75:
                        low_confidence_responses.append(response_data)

    print(f"\nUser questions: {len(user_questions)}")
    print(f"Assistant responses with sources: {len(all_responses)}")
    print(f"Low confidence responses (<75%): {len(low_confidence_responses)}")

    # Analyze by help_type
    admin_questions = [q for q in user_questions if q["help_type"] == "admin"]
    user_type_questions = [q for q in user_questions if q["help_type"] == "user"]

    print("\n--- By Context ---")
    print(f"Admin help questions: {len(admin_questions)}")
    print(f"User help questions: {len(user_type_questions)}")

    # ============================================
    # SECTION 1: LOW CONFIDENCE RESPONSES
    # ============================================
    print(f"\n{'=' * 60}")
    print("LOW CONFIDENCE RESPONSES (Similarity < 75%)")
    print(f"{'=' * 60}\n")

    # Sort by similarity (lowest first)
    low_confidence_responses.sort(key=lambda x: x["avg_similarity"])

    for i, resp in enumerate(low_confidence_responses, 1):
        print(f"\n--- Response #{i} (Similarity: {resp['avg_similarity']:.1%}) ---")
        print(f"Context: {resp['help_type'].upper()}")
        print(f"Timestamp: {resp['timestamp']}")

        # Show sources that were matched
        print("Sources matched:")
        for source in resp["sources"]:
            print(
                f"  - {source.get('title', 'Unknown')} / {source.get('section', 'Unknown')} ({source.get('similarity', 0):.1%})"
            )

        # Show preview of response
        response_preview = resp["response"][:300].replace("\n", " ")
        print(f"Response preview: {response_preview}...")

        # Show feedback if any
        if resp["feedback"]:
            feedback_text = "👍 Positive" if resp["feedback"] == 1 else "👎 Negative"
            print(f"User feedback: {feedback_text}")

    # ============================================
    # SECTION 2: ALL USER QUESTIONS
    # ============================================
    print(f"\n\n{'=' * 60}")
    print("ALL USER QUESTIONS")
    print(f"{'=' * 60}\n")

    # Group questions by topic keywords
    topic_keywords = {
        "theme": ["theme", "color", "branding", "logo", "css", "style", "appearance"],
        "documents": ["document", "upload", "file", "pdf", "processing", "knowledge"],
        "users": ["user", "account", "invite", "permission", "role", "admin"],
        "conversations": ["conversation", "chat", "message", "export", "history"],
        "kpi": [
            "kpi",
            "metric",
            "analytics",
            "dashboard",
            "ideation",
            "bradbury",
            "correction",
            "impact",
        ],
        "help_system": ["help", "documentation", "index", "reindex", "chunk"],
        "ai": ["ai", "claude", "llm", "response", "instruction", "prompt", "template"],
        "projects": ["project", "idea", "create", "trips"],
        "technical": ["api", "database", "supabase", "error", "bug", "issue"],
        "image": ["image", "generate", "picture", "dall-e", "visual"],
    }

    categorized = defaultdict(list)
    uncategorized = []

    for q in user_questions:
        question_lower = q["question"].lower()
        found_category = False

        for category, keywords in topic_keywords.items():
            if any(kw in question_lower for kw in keywords):
                categorized[category].append(q)
                found_category = True
                break

        if not found_category:
            uncategorized.append(q)

    print("Questions by Topic Category:")
    print("-" * 40)
    for category, questions in sorted(categorized.items(), key=lambda x: -len(x[1])):
        print(f"\n{category.upper()} ({len(questions)} questions):")
        for q in questions[:5]:  # Show first 5 per category
            preview = q["question"][:100].replace("\n", " ")
            print(f"  [{q['help_type']}] {preview}")
        if len(questions) > 5:
            print(f"  ... and {len(questions) - 5} more")

    if uncategorized:
        print(f"\nUNCATEGORIZED ({len(uncategorized)} questions):")
        for q in uncategorized[:10]:
            preview = q["question"][:100].replace("\n", " ")
            print(f"  [{q['help_type']}] {preview}")

    # ============================================
    # SECTION 3: GAP ANALYSIS
    # ============================================
    print(f"\n\n{'=' * 60}")
    print("GAP ANALYSIS & RECOMMENDATIONS")
    print(f"{'=' * 60}\n")

    # Calculate confidence stats
    if all_responses:
        avg_overall = sum(r["avg_similarity"] for r in all_responses) / len(all_responses)
        print(f"Average confidence score: {avg_overall:.1%}")
        print(
            f"Low confidence rate: {len(low_confidence_responses) / len(all_responses) * 100:.1f}%"
        )

    # Identify topics with lowest confidence
    topic_confidence = defaultdict(list)

    for resp in all_responses:
        for source in resp["sources"]:
            title = source.get("title", "Unknown")
            similarity = source.get("similarity", 0)
            topic_confidence[title].append(similarity)

    print("\nDocuments by Average Match Confidence:")
    print("-" * 40)
    for doc, scores in sorted(
        topic_confidence.items(), key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0
    ):
        avg = sum(scores) / len(scores) if scores else 0
        status = "❌ LOW" if avg < 0.75 else "⚠️ MEDIUM" if avg < 0.85 else "✅ GOOD"
        print(f"  {status} {avg:.1%} - {doc} ({len(scores)} matches)")

    # Identify common questions without good matches
    print("\n\nQUESTIONS WITH POOR DOCUMENTATION MATCHES:")
    print("-" * 40)

    # Find the questions that led to low confidence responses
    msg_to_question = {}
    last_user_msg = {}

    for msg in sorted(messages, key=lambda x: x.get("timestamp", "")):
        conv_id = msg["conversation_id"]
        if msg["role"] == "user":
            last_user_msg[conv_id] = msg["content"]
        elif msg["role"] == "assistant":
            msg_to_question[msg["id"]] = last_user_msg.get(conv_id, "Unknown")

    # Map low confidence responses back to questions
    low_conf_questions = []
    for resp in low_confidence_responses:
        # Find the user question that preceded this response
        for msg in messages:
            if msg["id"] in [m["id"] for m in messages if m.get("role") == "assistant"]:
                # This is a simplification - ideally we'd track conversation flow
                pass

    print("\nBased on low confidence responses, these topics need better documentation:")

    # Analyze what sources were matched for low confidence
    source_gaps = defaultdict(int)
    for resp in low_confidence_responses:
        for source in resp["sources"]:
            title = source.get("title", "Unknown")
            source_gaps[title] += 1

    for doc, count in sorted(source_gaps.items(), key=lambda x: -x[1])[:10]:
        print(f"  • {doc} (matched {count}x with low confidence)")

    # ============================================
    # SECTION 4: SPECIFIC RECOMMENDATIONS
    # ============================================
    print(f"\n\n{'=' * 60}")
    print("DOCUMENTATION IMPROVEMENT RECOMMENDATIONS")
    print(f"{'=' * 60}\n")

    recommendations = []

    # Check question categories vs documentation
    high_volume_topics = [cat for cat, qs in categorized.items() if len(qs) >= 3]

    print("HIGH PRIORITY (topics with many questions):")
    for topic in high_volume_topics:
        count = len(categorized[topic])
        # Check if this topic has low confidence
        topic_low_conf = sum(
            1
            for r in low_confidence_responses
            if any(topic in str(s.get("title", "")).lower() for s in r["sources"])
        )
        if topic_low_conf > 0:
            print(
                f"  • {topic.upper()}: {count} questions, {topic_low_conf} low confidence responses"
            )
            recommendations.append(f"Expand documentation on {topic}")

    print("\nMEDIUM PRIORITY (uncategorized questions - may indicate missing topics):")
    if len(uncategorized) >= 3:
        print(f"  • {len(uncategorized)} questions don't match known topic categories")
        print("    Sample uncategorized questions:")
        for q in uncategorized[:3]:
            print(f"      - {q['question'][:80]}...")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total questions analyzed: {len(user_questions)}")
    print(f"Low confidence responses: {len(low_confidence_responses)}")
    if all_responses:
        print(f"Overall system confidence: {avg_overall:.1%}")
    print("\nTop documentation gaps to address:")
    for i, rec in enumerate(recommendations[:5], 1):
        print(f"  {i}. {rec}")


if __name__ == "__main__":
    # Check for required environment variables
    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"):
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables required")
        print("Run with: source .env && python scripts/analyze_help_gaps.py")
        sys.exit(1)

    analyze_help_data(days=90)
