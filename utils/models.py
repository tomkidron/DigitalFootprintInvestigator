"""Data models for OSINT results"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SocialProfile(BaseModel):
    """Social media profile data"""

    platform: str
    username: str
    url: str
    followers: Optional[int] = None
    bio: Optional[str] = None
    verified: bool = False
    created_at: Optional[datetime] = None


class SearchResult(BaseModel):
    """Generic search result"""

    title: str
    url: str
    snippet: str
    source: str = "google"


class EmailData(BaseModel):
    """Email discovery data"""

    email: str
    source: str
    verified: bool = False
    breached: bool = False
    breach_count: int = 0


class OSINTResult(BaseModel):
    """Complete OSINT investigation result"""

    target: str
    target_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    profiles: List[SocialProfile] = []
    emails: List[EmailData] = []
    search_results: List[SearchResult] = []
    raw_data: dict = {}
