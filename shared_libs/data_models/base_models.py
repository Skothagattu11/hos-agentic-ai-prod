"""
Data models for health agent
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


# Pydantic models for data structure
class ScoreData(BaseModel):
    id: str
    profile_id: str
    type: str
    score: float
    data: Dict[str, Any]
    score_date_time: str  # Changed to str since it's text in DB
    created_at: datetime
    updated_at: datetime

class ArchetypeData(BaseModel):
    id: str
    profile_id: str
    name: str
    periodicity: str
    value: str
    data: Dict[str, Any]
    start_date_time: datetime
    end_date_time: datetime
    created_at: datetime
    updated_at: datetime

class BiomarkerData(BaseModel):
    id: str
    profile_id: str
    category: str
    type: str
    data: Dict[str, Any]
    start_date_time: datetime
    end_date_time: datetime
    created_at: datetime
    updated_at: datetime

class UserProfileContext(BaseModel):
    user_id: str
    scores: List[ScoreData]
    archetypes: List[ArchetypeData]
    biomarkers: List[BiomarkerData]
    date_range: Dict[str, datetime]