# D-01…D-04: Driver flows (Telegram only)

> Spec status: `accepted` (as-built inventory) · Platforms: **telegram only**

| ID | Flow | Code |
|----|------|------|
| D-01 | Registration / approval | `handlers/driver/registration.py` |
| D-02 | Online/offline + live location | `availability.py` |
| D-03 | Job offer accept/decline | `job_offer.py` · CARD-26 |
| D-04 | Picked up / delivered | job_offer + order status |

**Mask:** `driver_dispatch` TG only. LINE/IG customers never see driver console.
