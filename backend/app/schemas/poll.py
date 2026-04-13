from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

_camel_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class VoteRequest(BaseModel):
    selected_option: Literal["A", "B"]


class VoteResponse(BaseModel):
    model_config = _camel_config

    poll_id: str
    selected_option: Literal["A", "B"]
    option_a_count: int
    option_b_count: int
    reward_eligible: bool
