import json
import re
import logging

logger = logging.getLogger(__name__)

BOARD_COLUMNS = ["Backlog", "Scoped", "Designed", "Developed", "Tested", "Validated", "Documented"]

# Maps agent name → the column stories move TO when that agent completes
AGENT_TRANSITIONS = {
    "business_analyst": "Backlog",
    "product_owner": "Scoped",
    "architect": "Designed",
    "backend_developer": "Developed",
    "qa_tester": "Tested",
    "business_validator": "Validated",
    "technical_writer": "Documented",
}


def build_board_state(processed_artifacts):
    """
    Derive board state from artifacts produced so far.
    Each agent's output is parsed to determine which stories move where.

    Returns:
        {
            "columns": {"Backlog": [...], "Scoped": [...], ...},
            "stories": {"US-001": {id, title, points, priority, column, epic}, ...},
            "transitions": [{"story_id": "US-001", "from": "Backlog", "to": "Scoped", "agent": "product_owner"}, ...]
        }
    """
    all_stories = {}
    transitions = []

    # Step 1: Extract stories from Business Analyst backlog
    if "business_analyst" in processed_artifacts:
        stories = _extract_stories_from_backlog(processed_artifacts["business_analyst"])
        for s in stories:
            s["column"] = "Backlog"
            all_stories[s["id"]] = s

    # Step 2: Product Owner scopes MVP — move selected stories to Scoped
    if "product_owner" in processed_artifacts and all_stories:
        mvp_ids = _extract_mvp1_story_ids(processed_artifacts["product_owner"])
        for sid in mvp_ids:
            if sid in all_stories:
                old_col = all_stories[sid]["column"]
                all_stories[sid]["column"] = "Scoped"
                transitions.append({"story_id": sid, "from": old_col, "to": "Scoped", "agent": "product_owner"})

    # Step 3: Architect — all Scoped stories move to Designed
    if "architect" in processed_artifacts and all_stories:
        for sid, s in all_stories.items():
            if s["column"] == "Scoped":
                s["column"] = "Designed"
                transitions.append({"story_id": sid, "from": "Scoped", "to": "Designed", "agent": "architect"})

    # Step 4: Backend Developer — all Designed stories move to Developed
    # (We use backend_developer as the gate since it typically finishes after frontend)
    if "backend_developer" in processed_artifacts and all_stories:
        for sid, s in all_stories.items():
            if s["column"] == "Designed":
                s["column"] = "Developed"
                transitions.append({"story_id": sid, "from": "Designed", "to": "Developed", "agent": "backend_developer"})

    # Step 5: QA Tester — only passing stories move to Tested
    if "qa_tester" in processed_artifacts and all_stories:
        passing_ids = _extract_passing_story_ids(processed_artifacts["qa_tester"])
        for sid, s in all_stories.items():
            if s["column"] == "Developed":
                if sid in passing_ids:
                    s["column"] = "Tested"
                    transitions.append({"story_id": sid, "from": "Developed", "to": "Tested", "agent": "qa_tester"})

    # Step 6: Business Validator — covered stories move to Validated
    if "business_validator" in processed_artifacts and all_stories:
        validated_ids = _extract_validated_story_ids(processed_artifacts["business_validator"])
        for sid, s in all_stories.items():
            if s["column"] == "Tested":
                if not validated_ids or sid in validated_ids:
                    # If we couldn't parse specific IDs, move all Tested stories
                    s["column"] = "Validated"
                    transitions.append({"story_id": sid, "from": "Tested", "to": "Validated", "agent": "business_validator"})

    # Step 7: Technical Writer — all Validated stories move to Documented
    if "technical_writer" in processed_artifacts and all_stories:
        for sid, s in all_stories.items():
            if s["column"] == "Validated":
                s["column"] = "Documented"
                transitions.append({"story_id": sid, "from": "Validated", "to": "Documented", "agent": "technical_writer"})

    # Build columns dict
    columns = {col: [] for col in BOARD_COLUMNS}
    for sid, s in all_stories.items():
        columns[s["column"]].append(s)

    return {
        "columns": columns,
        "stories": all_stories,
        "transitions": transitions,
    }


def _extract_stories_from_backlog(content):
    """Parse BA's JSON output to extract user stories."""
    try:
        data = _parse_json_from_content(content)
        if not data:
            return []

        backlog = data.get("product_backlog", data)
        stories = []
        for epic in backlog.get("epics", []):
            for story in epic.get("stories", []):
                stories.append({
                    "id": story.get("story_id", ""),
                    "title": story.get("title", story.get("story", "")[:60]),
                    "points": story.get("story_points", 0),
                    "priority": story.get("priority", ""),
                    "epic": epic.get("name", ""),
                    "epic_id": story.get("epic_id", epic.get("epic_id", "")),
                })
        logger.info("Extracted %d stories from backlog", len(stories))
        return stories
    except Exception as e:
        logger.warning("Failed to extract stories from backlog: %s", e)
        return []


def _extract_mvp1_story_ids(content):
    """Parse PO's JSON output to get MVP-1 story IDs."""
    try:
        data = _parse_json_from_content(content)
        if not data:
            return []

        mvp_plan = data.get("mvp_plan", data)
        mvps = mvp_plan.get("mvps", [])
        if mvps:
            ids = mvps[0].get("stories", [])
            logger.info("Extracted %d MVP-1 story IDs", len(ids))
            return ids
        return []
    except Exception as e:
        logger.warning("Failed to extract MVP story IDs: %s", e)
        return []


def _extract_passing_story_ids(content):
    """Parse QA's JSON output to get story IDs where all tests pass."""
    try:
        data = _parse_json_from_content(content)
        if not data:
            return set()

        test_results = data.get("test_results", data)
        test_cases = test_results.get("test_cases", [])

        # Group tests by story_id
        story_tests = {}
        for tc in test_cases:
            sid = tc.get("story_id", "")
            if sid:
                if sid not in story_tests:
                    story_tests[sid] = []
                story_tests[sid].append(tc.get("status", "untested"))

        # A story passes if all its tests pass (or are untested)
        passing = set()
        for sid, statuses in story_tests.items():
            if all(s in ("pass", "untested") for s in statuses):
                passing.add(sid)

        logger.info("Extracted %d passing story IDs from QA", len(passing))
        return passing
    except Exception as e:
        logger.warning("Failed to extract passing story IDs: %s", e)
        return set()


def _extract_validated_story_ids(content):
    """Parse Business Validator's markdown to find covered story IDs."""
    try:
        # Look for US-XXX references in rows containing "Covered"
        validated = set()
        for line in content.split("\n"):
            if "Covered" in line or "covered" in line:
                ids = re.findall(r"US-\d+", line)
                validated.update(ids)

        # Also check for "APPROVED" verdict — if approved, all stories are validated
        if "APPROVED" in content and not validated:
            # Return empty set to signal "validate all" in the caller
            return set()

        logger.info("Extracted %d validated story IDs", len(validated))
        return validated
    except Exception as e:
        logger.warning("Failed to extract validated story IDs: %s", e)
        return set()


def _parse_json_from_content(content):
    """Try to parse JSON from content that may be wrapped in markdown code fences."""
    content = content.strip()

    # Strip markdown code fences
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first and last lines if they are fences
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON object in the content
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None
