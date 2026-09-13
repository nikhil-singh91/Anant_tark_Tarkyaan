"""
Task Planner Subsystem.
Decomposes high-level learner objectives into bounded, risk-classified, verifiable agent steps.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from tarkyaan.agent.task_models import AgentStep, AutonomousTask, TaskGoal
from tarkyaan.context.multimodal_context import MultimodalContext
from tarkyaan.models.enums import AgentRiskLevel, AgentStepStatus, AgentTaskStatus


class TaskPlanner:
    """
    Decomposes user and educational goals into structured, bounded step plans.
    Assigns risk tiers, required capabilities, and verification criteria to each step.
    """

    def plan_task(
        self,
        learner_id: str,
        goal_text: str,
        context: Optional[MultimodalContext] = None,
        max_steps: int = 10,
    ) -> AutonomousTask:
        """
        Create a structured AutonomousTask from a goal string and active multimodal context.
        """
        task_id = f"atask_{uuid.uuid4().hex[:8]}"
        goal_lower = goal_text.lower()

        goal = TaskGoal(
            description=goal_text,
            target_concept=context.learner.active_topic if context else "general_cs",
            risk_level=AgentRiskLevel.LOW,
        )

        steps: List[AgentStep] = []

        # 1. Scenario: Project Debugging ("Find why my code isn't working", "Debug error")
        if any(w in goal_lower for w in ["debug", "error", "failing", "not working", "why my code"]):
            goal.risk_level = AgentRiskLevel.HIGH
            steps = [
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=1,
                    action="observe_screen_and_project",
                    capability_id="screen.capture_and_analyze",
                    description="Inspect active IDE screen and error output for failure signals.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Visual error code or stack trace extracted.",
                ),
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=2,
                    action="inspect_source_file",
                    capability_id="fs.read_code",
                    description="Read the relevant source code file containing the suspect line.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Source code successfully read into context.",
                ),
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=3,
                    action="diagnose_and_explain_bug",
                    capability_id="teaching.explain_misconception",
                    description="Synthesize error cause and explain logic flaw to learner.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Pedagogical explanation formulated with Socratic hint.",
                ),
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=4,
                    action="run_safe_verification",
                    capability_id="sandbox.execute_python",
                    description="Run isolated verification test in sandbox to confirm solution.",
                    risk_level=AgentRiskLevel.MEDIUM,
                    verification_criteria="Sandbox test passes with exit code 0.",
                ),
            ]

        # 2. Scenario: Codebase / Project Explanation ("Open my project", "Teach me this project")
        elif any(w in goal_lower for w in ["teach me this project", "open my", "codebase", "architecture"]):
            steps = [
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=1,
                    action="open_application",
                    capability_id="app.control",
                    parameters={"app_name": "Visual Studio Code"},
                    description="Launch or focus Visual Studio Code on the project.",
                    risk_level=AgentRiskLevel.MEDIUM,
                    verification_criteria="VS Code is active and running.",
                ),
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=2,
                    action="inspect_project_structure",
                    capability_id="fs.inspect_project",
                    description="Analyze workspace file hierarchy and identify entry points.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Project structure mapped with files and directories.",
                ),
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=3,
                    action="explain_codebase_architecture",
                    capability_id="teaching.explain_concept",
                    description="Provide comprehensive architectural walkthrough tailored to learner.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Educational architectural walkthrough generated.",
                ),
            ]

        # 3. Scenario: Research & Resource Finding ("Find me a better explanation of DP")
        elif any(w in goal_lower for w in ["find", "search", "resource", "better explanation", "research"]):
            steps = [
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=1,
                    action="search_web_resources",
                    capability_id="browser.session_navigate",
                    parameters={"query": goal_text},
                    description="Search verified academic and educational sources.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Candidate resources retrieved from search index.",
                ),
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=2,
                    action="evaluate_and_rank_resources",
                    capability_id="research.curate",
                    description="Rank candidates against learner's mastery level and style preferences.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Top-fit educational resources selected.",
                ),
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=3,
                    action="synthesize_curated_explanation",
                    capability_id="teaching.adaptive_explanation",
                    description="Synthesize curated resource into personalized lesson.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Personalized lesson synthesized.",
                ),
            ]

        # 4. Default: Adaptive Study / Preparation ("Help me prepare for my DSA exam", "Study session")
        else:
            steps = [
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=1,
                    action="inspect_mastery_and_gaps",
                    capability_id="learning.inspect_state",
                    description="Inspect active learning roadmap, mastery decay, and at-risk concepts.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Identified highest-leverage topic.",
                ),
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=2,
                    action="conduct_teaching_session",
                    capability_id="teaching.socratic_inquiry",
                    description="Engage in adaptive explanation and Socratic dialogue.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Teaching turn delivered to learner.",
                ),
                AgentStep(
                    step_id=f"astep_{uuid.uuid4().hex[:6]}",
                    task_id=task_id,
                    step_index=3,
                    action="generate_practice_challenge",
                    capability_id="practice.present_question",
                    description="Generate targeted practice challenge for concept reinforcement.",
                    risk_level=AgentRiskLevel.LOW,
                    verification_criteria="Practice problem presented.",
                ),
            ]

        return AutonomousTask(
            task_id=task_id,
            learner_id=learner_id,
            goal=goal,
            status=AgentTaskStatus.PLANNING,
            steps=steps[:max_steps],
            max_steps=max_steps,
        )
