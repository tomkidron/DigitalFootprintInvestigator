"""State for LangGraph OSINT workflow"""
from typing import TypedDict, Annotated
import operator


class OSINTState(TypedDict):
    """Investigation state"""
    target: str
    google_data: Annotated[list, operator.add]
    social_data: Annotated[list, operator.add]
    analysis: str
    report: str
