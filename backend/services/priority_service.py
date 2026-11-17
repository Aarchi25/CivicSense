"""MongoDB stages for the shared complaint priority ordering."""


def priority_sort_pipeline() -> list[dict]:
    """Sort unresolved complaints first, then highest urgency and oldest report."""
    return [
        {
            "$addFields": {
                "_resolvedPriority": {
                    "$cond": [{"$eq": ["$status", "resolved"]}, 1, 0]
                }
            }
        },
        {
            "$sort": {
                "_resolvedPriority": 1,
                "urgencyScore": -1,
                "createdAt": 1,
            }
        },
        {"$project": {"_resolvedPriority": 0}},
    ]
