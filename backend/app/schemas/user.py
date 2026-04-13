from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


RewardType = Literal["vote", "ad", "share"]
TransactionStatus = Literal["pending", "success", "failed"]

_camel_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UserSchema(BaseModel):
    model_config = _camel_config

    id: str
    toss_user_id: str
    is_premium: bool
    total_points: int
    today_earned: int
    created_at: datetime


class PointTransactionSchema(BaseModel):
    model_config = _camel_config

    id: str
    amount: int
    reason: RewardType
    status: TransactionStatus
    created_at: datetime


class UserProfileResponse(BaseModel):
    model_config = _camel_config

    user: UserSchema
    transactions: list[PointTransactionSchema]


class RewardRequest(BaseModel):
    reward_type: RewardType
    reference_id: str


class RewardResponse(BaseModel):
    model_config = _camel_config

    transaction_id: str
    amount: int
    status: TransactionStatus
    current_balance: int
