import logging
from typing import Annotated, List, Dict, Optional

import chalk
from pydantic import Field


class ThoughtData:
    def __init__(self, **kwargs):
        self.thought: str = kwargs['thought']
        self.next_thought_needed: bool = kwargs['next_thought_needed']
        self.thought_number: int = kwargs['thought_number']
        self.total_thoughts: int = kwargs['total_thoughts']
        self.is_revision: bool = kwargs['is_revision']
        self.revises_thought: int = kwargs['revises_thought']
        self.branch_from_thought: int = kwargs['branch_from_thought']
        self.branch_id: str = kwargs['branch_id']
        self.needs_more_thoughts: bool = kwargs['needs_more_thoughts']


disable_thought_logging: bool = False
thought_history: List[ThoughtData] = []
branches: Dict[str, List[ThoughtData]] = {}


def format_thought(thought_data: ThoughtData) -> str:
    if thought_data.is_revision:
        prefix = chalk.yellow('🔄 Revision')
        context = f" (revising thought {thought_data.revises_thought})"
    elif thought_data.branch_from_thought:
        prefix = chalk.green('🌿 Branch')
        context = f" (from thought {thought_data.branch_from_thought}, ID: {thought_data.branch_id})"
    else:
        prefix = chalk.blue('💭 Thought')
        context = ''

    header = f"{prefix} {thought_data.thought_number}/{thought_data.total_thoughts}{context}"
    border = '─' * (max(len(header), len(thought_data.thought)) + 4)

    return f"""
┌{border}┐
│ {header} │
├{border}┤
│ {thought_data.thought.ljust(len(border) - 2), ' '} │
└{border}┘
"""


def process_thought(
        thought: Annotated[str, Field(description="Your current thinking step")],
        next_thought_needed: Annotated[bool, Field(description="Whether another thought step is needed")],
        thought_number: Annotated[int, Field(description="Current thought number", gt=0)],
        total_thoughts: Annotated[int, Field(description="Estimated total thoughts needed", gt=0)],
        is_revision: Annotated[bool, Field(description="Whether this revises previous thinking", default=False)],
        revises_thought: Annotated[int, Field(description="Which thought is being reconsidered", gt=0, default=1)],
        branch_from_thought: Annotated[int, Field(description="Branching point thought number", gt=0, default=1)],
        branch_id: Annotated[str, Field(description="Branch identifier", default="")],
        needs_more_thoughts: Annotated[bool, Field(description="If more thoughts are needed", default=False)]
):
    try:
        thought_data = ThoughtData(thought=thought,
                                   next_thought_needed=next_thought_needed,
                                   thought_number=thought_number,
                                   total_thoughts=total_thoughts,
                                   is_revision=is_revision,
                                   revises_thought=revises_thought,
                                   branch_from_thought=branch_from_thought,
                                   branch_id=branch_id,
                                   needs_more_thoughts=needs_more_thoughts)
        logging.error(thought_data)

        if thought_data.thought_number > thought_data.total_thoughts:
            thought_data.total_thoughts = thought_data.thought_number

        thought_history.append(thought_data)

        if thought_data.branch_from_thought and len(thought_data.branch_id) != 0:
            if not branches[thought_data.branch_id]:
                branches[thought_data.branch_id] = []
            branches[thought_data.branch_id].append(thought_data)

        if not disable_thought_logging:
            formatted_thought = format_thought(thought_data)
            logging.error(formatted_thought)

        return {
            "thoughtNumber": thought_data.thought_number,
            "totalThoughts": thought_data.total_thoughts,
            "nextThoughtNeeded": thought_data.next_thought_needed,
            "branches": list(branches.keys()),
            "thoughtHistoryLength": len(thought_history)
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": 'failed'
        }


def send_request():
    return ("sequentialthinking",
            {"thought": "1.test",
             "next_thought_needed": True,
             "thought_number": 1,
             "total_thoughts": 3})
