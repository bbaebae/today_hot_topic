from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..database import db
from ..schemas.poll import VoteRequest, VoteResponse

router = APIRouter()


@router.post("/{poll_id}/vote", response_model=VoteResponse)
async def vote(
    poll_id: str,
    body: VoteRequest,
    user: dict = Depends(get_current_user),
):
    client = db()

    # Check poll exists
    poll_res = (
        client.table("polls")
        .select("*")
        .eq("id", poll_id)
        .maybe_single()
        .execute()
    )
    if not poll_res.data:
        raise HTTPException(status_code=404, detail="Poll not found")

    poll = poll_res.data

    # Idempotency: already voted?
    existing = (
        client.table("vote_logs")
        .select("id")
        .eq("poll_id", poll_id)
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )
    if existing.data:
        # Return current counts (already voted)
        return VoteResponse(
            poll_id=poll_id,
            selected_option=body.selected_option,
            option_a_count=poll["option_a_count"],
            option_b_count=poll["option_b_count"],
        )

    # Record the vote
    client.table("vote_logs").insert(
        {
            "id": str(uuid.uuid4()),
            "poll_id": poll_id,
            "user_id": user["id"],
            "selected_option": body.selected_option,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()

    # Increment the chosen option counter
    col = "option_a_count" if body.selected_option == "A" else "option_b_count"
    new_count = poll[col] + 1
    client.table("polls").update({col: new_count}).eq("id", poll_id).execute()

    option_a = poll["option_a_count"] + (1 if body.selected_option == "A" else 0)
    option_b = poll["option_b_count"] + (1 if body.selected_option == "B" else 0)

    return VoteResponse(
        poll_id=poll_id,
        selected_option=body.selected_option,
        option_a_count=option_a,
        option_b_count=option_b,
    )
