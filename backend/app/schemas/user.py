from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


_camel_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class UserSchema(BaseModel):
    model_config = _camel_config

    id: str
    toss_user_id: str
    is_premium: bool
    created_at: datetime


class UserProfileResponse(BaseModel):
    model_config = _camel_config

    user: UserSchema
