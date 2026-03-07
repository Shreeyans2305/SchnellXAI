from fastapi import APIRouter

from data.seed import get_live_state

router = APIRouter()


@router.get("/carriers")
def get_carriers():
    carriers = get_live_state().get("carriers", [])
    out = []
    for c in carriers:
        r = int(c.get("reliability", 85))
        out.append(
            {
                **c,
                "trend": [max(60, r - 4), max(60, r - 2), max(60, r - 1), r, max(60, r - 1), r, min(99, r + 1)],
                "logo": "".join(part[0] for part in str(c.get("name", "C")).split()[:2]).upper()[:2],
            }
        )
    return out
