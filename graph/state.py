"""State for LangGraph OSINT workflow"""

import operator
from typing import Annotated, Optional, TypedDict


class OSINTState(TypedDict):
    """Investigation state"""

    target: str
    config: Optional[dict]  # Configuration including advanced analysis flags
    google_data: Annotated[list, operator.add]
    social_data: Annotated[list, operator.add]
    analysis: str
    report: str
    # Advanced analysis results (only populated if enabled)
    timeline_data: Optional[dict]
    network_data: Optional[dict]
