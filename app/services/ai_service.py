"""
AI Priority Service — uses Claude to suggest task priorities and groupings.
"""
import json
import logging

import anthropic

from app.core.config import settings
from app.models.task import TaskPriority

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a productivity assistant. Given a list of tasks, 
analyze them and suggest priorities based on urgency, importance, and due dates.
You MUST respond with valid JSON only — no prose, no markdown, no explanation.

Return this exact structure:
{
  "suggestions": [
    {
      "task_id": "<id>",
      "suggested_priority": "urgent|high|medium|low",
      "reason": "<short reason, max 15 words>"
    }
  ],
  "groups": {
    "do_today": ["<task_id>", ...],
    "this_week": ["<task_id>", ...],
    "backlog": ["<task_id>", ...]
  },
  "summary": "<2 sentence overall summary>"
}"""


async def get_ai_priority_suggestions(tasks: list[dict]) -> dict:
    """
    Call Claude to analyze tasks and return priority suggestions.
    Falls back to a rule-based response if API key is not set.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set — returning rule-based suggestions")
        return _rule_based_fallback(tasks)

    if not tasks:
        return {"suggestions": [], "groups": {"do_today": [], "this_week": [], "backlog": []}, "summary": "No tasks to analyze."}

    task_descriptions = "\n".join(
        f"- ID: {t['id']} | Title: {t['title']} | "
        f"Status: {t['status']} | Priority: {t['priority']} | "
        f"Due: {t.get('due_date', 'none')}"
        for t in tasks
    )

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        message = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze these tasks and suggest priorities:\n\n{task_descriptions}",
                }
            ],
        )

        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        return _rule_based_fallback(tasks)
    except Exception as e:
        logger.error(f"AI priority service error: {e}")
        return _rule_based_fallback(tasks)


def _rule_based_fallback(tasks: list[dict]) -> dict:
    """Simple rule-based priority fallback when AI is unavailable."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    suggestions = []
    do_today = []
    this_week = []
    backlog = []

    for t in tasks:
        task_id = t["id"]
        due = t.get("due_date")
        current_priority = t.get("priority", "medium")

        suggested = current_priority
        reason = "No change suggested"

        if due:
            try:
                due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
                delta = due_dt - now
                if delta.total_seconds() < 0:
                    suggested = TaskPriority.URGENT
                    reason = "Task is overdue"
                    do_today.append(task_id)
                elif delta < timedelta(days=1):
                    suggested = TaskPriority.URGENT
                    reason = "Due within 24 hours"
                    do_today.append(task_id)
                elif delta < timedelta(days=7):
                    suggested = TaskPriority.HIGH
                    reason = "Due within this week"
                    this_week.append(task_id)
                else:
                    backlog.append(task_id)
            except (ValueError, AttributeError):
                backlog.append(task_id)
        else:
            backlog.append(task_id)

        suggestions.append({
            "task_id": task_id,
            "suggested_priority": suggested,
            "reason": reason,
        })

    return {
        "suggestions": suggestions,
        "groups": {"do_today": do_today, "this_week": this_week, "backlog": backlog},
        "summary": f"Analyzed {len(tasks)} tasks using rule-based fallback. Set ANTHROPIC_API_KEY for AI suggestions.",
    }
