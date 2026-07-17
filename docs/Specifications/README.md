# Conversation & Workflow Specifications

> **Source of truth for chat interactions and workflows.**
> Owned by **[CARD-34](../done/CARD-34-conversation-workflow-specifications.md)**.
> Multi-channel plan: [MULTI-CHANNEL-TIERED-PLAN.md](../later/MULTI-CHANNEL-TIERED-PLAN.md).
> **Backend law:** [UNIFIED-BACKEND-CHANNEL-INTERFACE.md](UNIFIED-BACKEND-CHANNEL-INTERFACE.md).

**Default mode:** document **as-built** flows; adapters only for I/O. Capability masks define LINE / IG / web subsets.

| Resource | Path |
|----------|------|
| Flow template | [`_TEMPLATE-FLOW.md`](_TEMPLATE-FLOW.md) |
| Flow docs | [`flows/`](flows/) |
| Cross-cutting | [`cross-cutting/`](cross-cutting/) |
| Platform masks | [`cross-cutting/platform-masks.md`](cross-cutting/platform-masks.md) |
| IG package | [`flows/PACKAGE-instagram.md`](flows/PACKAGE-instagram.md) |
| LINE package | [`flows/PACKAGE-line.md`](flows/PACKAGE-line.md) |
| Deep specs | [AI-CUSTOMER-ASSISTANT.md](AI-CUSTOMER-ASSISTANT.md), [MENU-SYSTEM.md](MENU-SYSTEM.md), [WEB-INSTAGRAM-STYLE-STOREFRONT.md](WEB-INSTAGRAM-STYLE-STOREFRONT.md), … |
| Session start | [../CLEAR-START.md](../CLEAR-START.md) |

---

## Status legend

| Status | Meaning |
|--------|---------|
| `missing` | Not written |
| `draft` | First pass |
| `reviewed` | Checked vs code |
| `accepted` | Ready to gate multi-channel |
| `linked` | Covered by existing deep-spec |

---

## Customer flows

| ID | Name | Status | Spec |
|----|------|--------|------|
| C-01 | Start / main menu / profile | accepted | [flows/C-01.md](flows/C-01.md) |
| C-02 | Language picker | accepted | [flows/C-02.md](flows/C-02.md) |
| C-03 | Privacy / PDPA | accepted | [flows/C-03.md](flows/C-03.md) |
| C-04 | Rules / help | accepted | [flows/C-04.md](flows/C-04.md) |
| C-05 | Store / brand selection | accepted | [flows/C-05.md](flows/C-05.md) |
| C-06 | Browse shop | accepted | [flows/C-06.md](flows/C-06.md) |
| C-07 | Product search | accepted | [flows/C-07.md](flows/C-07.md) |
| C-08 | Cart + modifiers | accepted | [flows/C-08.md](flows/C-08.md) |
| C-09 | Saved carts | accepted | [flows/C-09.md](flows/C-09.md) |
| C-10 | Checkout — location | accepted | [flows/C-10.md](flows/C-10.md) |
| C-11 | Checkout — delivery type | accepted | [flows/C-11.md](flows/C-11.md) |
| C-12 | Checkout — phone / address / note | accepted | [flows/C-12.md](flows/C-12.md) |
| C-13 | Payment — cash | accepted | [flows/C-13.md](flows/C-13.md) |
| C-14 | Payment — PromptPay + slip | accepted | [flows/C-14.md](flows/C-14.md) |
| C-15 | Payment — crypto | accepted | [flows/C-15.md](flows/C-15.md) |
| C-16 | Bonus at checkout | accepted | [flows/C-16.md](flows/C-16.md) |
| C-17 | My orders / reorder | accepted | [flows/C-17.md](flows/C-17.md) |
| C-18 | Order status notifications | accepted | [flows/C-18.md](flows/C-18.md) |
| C-19 | Delivery chat + live location | accepted | [flows/C-19.md](flows/C-19.md) |
| C-20 | Reviews | accepted | [flows/C-20.md](flows/C-20.md) |
| C-21 | Referrals | accepted | [flows/C-21.md](flows/C-21.md) |
| C-22 | Support tickets | accepted | [flows/C-22.md](flows/C-22.md) |
| C-23 | Customer AI | linked | [AI-CUSTOMER-ASSISTANT.md](AI-CUSTOMER-ASSISTANT.md) · [flows/C-23.md](flows/C-23.md) |
| C-24 | Coupons | accepted | [flows/C-24.md](flows/C-24.md) |

---

## Admin / ops (Telegram only)

| ID | Name | Status | Spec |
|----|------|--------|------|
| A-01…A-12 | Ops inventory | accepted | [flows/A-ops-inventory.md](flows/A-ops-inventory.md) |

---

## Driver (Telegram only)

| ID | Name | Status | Spec |
|----|------|--------|------|
| D-01…D-04 | Driver inventory | accepted | [flows/D-driver-inventory.md](flows/D-driver-inventory.md) |

---

## Web storefront

| ID | Name | Status | Spec |
|----|------|--------|------|
| W-01…W-03 | Storefront | draft/linked | [flows/W-web-storefront.md](flows/W-web-storefront.md) · [WEB-INSTAGRAM-STYLE-STOREFRONT.md](WEB-INSTAGRAM-STYLE-STOREFRONT.md) |

---

## Cross-cutting

| Doc | Status |
|-----|--------|
| [identity-and-locale](cross-cutting/identity-and-locale.md) | accepted |
| [order-status-machine](cross-cutting/order-status-machine.md) | accepted |
| [payment-methods](cross-cutting/payment-methods.md) | accepted |
| [error-and-back-navigation](cross-cutting/error-and-back-navigation.md) | accepted |
| [platform-masks](cross-cutting/platform-masks.md) | accepted |

---

## Channel packages (hard gates)

| Package | Status |
|---------|--------|
| [Instagram In/Out](flows/PACKAGE-instagram.md) | accepted |
| [LINE In/Out](flows/PACKAGE-line.md) | accepted |

Last inventory pass: **2026-07-17** (CARD-34).
