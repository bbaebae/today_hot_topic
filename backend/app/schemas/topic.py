from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


Category = Literal["news", "story", "finance"]

_camel_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TopicBase(BaseModel):
    model_config = _camel_config

    id: str
    title: str
    category: Category
    image_url: str | None
    view_count: int
    rank: int
    created_at: datetime


class TopicListItem(TopicBase):
    pass


class PollSchema(BaseModel):
    model_config = _camel_config

    id: str
    topic_id: str
    option_a_text: str
    option_b_text: str
    option_a_count: int
    option_b_count: int
    user_voted: Literal["A", "B"] | None = None


class TopicDetail(TopicBase):
    source_url: str
    summary: list[str]
    poll: PollSchema


class TopicsResponse(BaseModel):
    topics: list[TopicListItem]
