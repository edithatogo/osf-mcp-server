"""Research prompts for OSF MCP Server."""

from typing import Any
import mcp.types as types


PROMPTS = {
    "analyze_project": types.Prompt(
        name="analyze_project",
        description="Analyze an OSF project for research quality and completeness",
        arguments=[
            types.PromptArgument(
                name="project_id",
                description="OSF project ID to analyze",
                required=True,
            ),
        ],
    ),
    "compare_registrations": types.Prompt(
        name="compare_registrations",
        description="Compare pre-registration with final study results",
        arguments=[
            types.PromptArgument(
                name="registration_id",
                description="Registration ID to analyze",
                required=True,
            ),
        ],
    ),
    "literature_review": types.Prompt(
        name="literature_review",
        description="Search OSF for relevant preprints and registrations on a topic",
        arguments=[
            types.PromptArgument(
                name="topic",
                description="Research topic to explore",
                required=True,
            ),
            types.PromptArgument(
                name="discipline",
                description="Academic discipline (e.g., psychology, biology)",
                required=False,
            ),
        ],
    ),
    "reproducibility_check": types.Prompt(
        name="reproducibility_check",
        description="Assess reproducibility of a research project",
        arguments=[
            types.PromptArgument(
                name="project_id",
                description="Project ID to assess",
                required=True,
            ),
        ],
    ),
}


async def list_prompts() -> list[types.Prompt]:
    """List all available prompts."""
    return list(PROMPTS.values())


async def get_prompt(
    name: str,
    arguments: dict[str, str] | None = None,
) -> types.GetPromptResult:
    """Get a specific prompt with arguments."""
    if name not in PROMPTS:
        raise ValueError(f"Unknown prompt: {name}")

    args = arguments or {}

    if name == "analyze_project":
        project_id = args.get("project_id", "")
        return types.GetPromptResult(
            description=f"Analyze OSF project {project_id}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Analyze the OSF project with ID '{project_id}' for research quality and completeness.

Please evaluate:
1. **Project Structure**: Are files well-organized? Is there a clear README?
2. **Documentation**: Is the methodology clearly explained?
3. **Data Availability**: Are datasets available and well-documented?
4. **Code Quality**: Is analysis code present and reproducible?
5. **Preregistration**: Is there a linked pre-registration?
6. **Contributors**: Who are the contributors and their roles?
7. **Openness**: Is the project appropriately open for its content?

First, use the get_project tool to retrieve project details, then list_files to see the file structure, and get_wiki for any documentation.

Provide a comprehensive assessment with specific recommendations for improvement.""",
                    ),
                ),
            ],
        )

    elif name == "compare_registrations":
        registration_id = args.get("registration_id", "")
        return types.GetPromptResult(
            description=f"Compare registration {registration_id} with outcomes",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Analyze the OSF registration '{registration_id}' and compare pre-registered plans with actual outcomes.

Please evaluate:
1. **Hypotheses**: Were the pre-registered hypotheses tested as planned?
2. **Methods**: Did the actual methods match the pre-registered protocol?
3. **Sample Size**: Was the planned sample size achieved?
4. **Analysis Plan**: Were analyses conducted as pre-specified?
5. **Deviations**: Document any deviations from the pre-registration
6. **Transparency**: How well are deviations explained?

Use search_registrations and get_project tools to gather information.

Provide a detailed comparison report highlighting consistencies and discrepancies.""",
                    ),
                ),
            ],
        )

    elif name == "literature_review":
        topic = args.get("topic", "")
        discipline = args.get("discipline", "")
        return types.GetPromptResult(
            description=f"Literature review on {topic}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Conduct a literature review on OSF for the topic: '{topic}'
{f"Discipline focus: {discipline}" if discipline else ""}

Please:
1. **Search Preprints**: Use search_preprints to find relevant preprints
2. **Search Registrations**: Use search_registrations to find pre-registered studies
3. **Search Projects**: Use search_projects to find ongoing research
4. **Synthesize Findings**: Summarize the current state of research
5. **Identify Gaps**: Note areas lacking pre-registered studies
6. **Key Researchers**: Identify prolific contributors in this area

For important papers, use download_file to get full text for detailed analysis.

Provide a structured literature review with:
- Overview of the field
- Major findings and trends
- Methodological approaches used
- Research gaps and opportunities
- Key citations with DOIs where available""",
                    ),
                ),
            ],
        )

    elif name == "reproducibility_check":
        project_id = args.get("project_id", "")
        return types.GetPromptResult(
            description=f"Reproducibility assessment of {project_id}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Assess the reproducibility of OSF project '{project_id}'.

Evaluate using the TOP Guidelines framework:
1. **Data Availability**: Can data be accessed? Is it documented?
2. **Code Availability**: Is analysis code provided and runnable?
3. **Materials**: Are experimental materials available?
4. **Design Transparency**: Is the study design clear and complete?
5. **Preregistration**: Is there a pre-registration? How detailed?
6. **Replication**: Has this been replicated or is replication possible?

Use these tools:
- get_project: Get project metadata
- list_files: Check available files
- download_file/read_file: Examine documentation
- get_wiki: Check project wiki

Provide:
- Reproducibility score (1-5 for each criterion)
- Specific strengths
- Areas needing improvement
- Actionable recommendations""",
                    ),
                ),
            ],
        )

    raise ValueError(f"Prompt '{name}' not implemented")
