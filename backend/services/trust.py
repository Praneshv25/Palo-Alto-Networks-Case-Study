def compute_trust_label(db, report_id):
    """Recompute and update the trust_label for a report based on vote counts."""
    row = db.execute(
        "SELECT upvotes, downvotes, is_ai_generated FROM safety_reports WHERE id = ?",
        (report_id,),
    ).fetchone()

    if row is None:
        return None

    upvotes = row["upvotes"]
    downvotes = row["downvotes"]
    is_ai = row["is_ai_generated"]

    if downvotes >= 3 and downvotes > upvotes:
        label = "flagged"
    elif upvotes >= 3 and upvotes > downvotes * 2:
        label = "community_verified"
    elif not is_ai:
        label = "pending_verification"
    else:
        label = "ai_generated"

    db.execute(
        "UPDATE safety_reports SET trust_label = ? WHERE id = ?",
        (label, report_id),
    )
    db.commit()
    return label
