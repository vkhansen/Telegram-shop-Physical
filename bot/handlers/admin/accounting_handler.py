"""
Admin Accounting / Revenue Export Handler.

Provides:
- Revenue summary (today / week / month / all time)
- Export Sales CSV
- Export Revenue by Product CSV
- Export Payment Reconciliation CSV
"""
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext

from bot.database.models.main import Permission
from bot.filters import HasPermissionFilter
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons
from bot.export.sales_report import (
    generate_sales_csv,
    generate_revenue_by_product_csv,
    generate_payment_reconciliation_csv,
    get_revenue_summary,
)

router = Router()

PERIOD_LABELS = {
    "today": "Today",
    "week": "Last 7 Days",
    "month": "Last 30 Days",
    "all": "All Time",
}


# ── Accounting menu ──────────────────────────────────────────────────

@router.callback_query(F.data == "admin_accounting", HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def admin_accounting(call: CallbackQuery, state: FSMContext):
    """Show the accounting / revenue menu."""
    await state.clear()
    actions = [
        (localize("admin.accounting.summary_today"), "accounting_summary_today"),
        (localize("admin.accounting.summary_week"), "accounting_summary_week"),
        (localize("admin.accounting.summary_month"), "accounting_summary_month"),
        (localize("admin.accounting.summary_all"), "accounting_summary_all"),
        (localize("admin.accounting.export_sales"), "accounting_export_sales"),
        (localize("admin.accounting.export_products"), "accounting_export_products"),
        (localize("admin.accounting.export_payments"), "accounting_export_payments"),
        (localize("btn.back"), "console"),
    ]
    await call.message.edit_text(
        localize("admin.accounting.title"),
        reply_markup=simple_buttons(actions, per_row=2),
    )


# ── Revenue summary ─────────────────────────────────────────────────

def _resolve_period(period: str):
    """Return (from_date, to_date) for the requested period."""
    now = datetime.now(timezone.utc)
    to_date = now
    if period == "today":
        from_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        from_date = now - timedelta(days=7)
    elif period == "month":
        from_date = now - timedelta(days=30)
    else:
        from_date = None
    return from_date, to_date


@router.callback_query(
    F.data.startswith("accounting_summary_"),
    HasPermissionFilter(permission=Permission.SHOP_MANAGE),
)
async def accounting_summary(call: CallbackQuery, state: FSMContext):
    """Display revenue summary for the selected period."""
    period = call.data.replace("accounting_summary_", "")
    from_date, to_date = _resolve_period(period)

    summary = await get_revenue_summary(from_date, to_date)

    period_label = PERIOD_LABELS.get(period, period)

    # Format payment breakdown lines
    payment_lines = "\n".join(
        f"  - {method}: {amount:.2f}"
        for method, amount in summary.get("by_payment", {}).items()
    ) or "  N/A"

    # Format top products lines
    top_lines = "\n".join(
        f"  {i}. {name} — {rev:.2f}"
        for i, (name, rev) in enumerate(summary.get("top_products", [])[:5], 1)
    ) or "  N/A"

    text = (
        f"{localize('admin.accounting.summary')}\n"
        f"<b>{period_label}</b>\n\n"
        f"<b>Total Revenue:</b> {summary.get('total_revenue', 0):.2f}\n"
        f"<b>Order Count:</b> {summary.get('order_count', 0)}\n"
        f"<b>Avg Order Value:</b> {summary.get('avg_value', 0):.2f}\n\n"
        f"<b>Breakdown by Payment:</b>\n{payment_lines}\n\n"
        f"<b>Top 5 Products:</b>\n{top_lines}"
    )

    await call.message.edit_text(
        text,
        reply_markup=back("admin_accounting"),
        parse_mode="HTML",
    )


# ── CSV exports ──────────────────────────────────────────────────────

EXPORT_GENERATORS = {
    "sales": generate_sales_csv,
    "products": generate_revenue_by_product_csv,
    "payments": generate_payment_reconciliation_csv,
}


@router.callback_query(
    F.data.startswith("accounting_export_"),
    HasPermissionFilter(permission=Permission.SHOP_MANAGE),
)
async def accounting_export(call: CallbackQuery, state: FSMContext):
    """Generate and send a CSV report as a document."""
    export_type = call.data.replace("accounting_export_", "")
    generator = EXPORT_GENERATORS.get(export_type)
    if generator is None:
        await call.answer(localize("admin.accounting.unknown_export"), show_alert=True)
        return

    csv_string = await generator()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{export_type}_report_{date_str}.csv"

    document = BufferedInputFile(csv_string.encode("utf-8"), filename=filename)
    await call.message.answer_document(
        document=document,
        caption=localize("admin.accounting.export_sent"),
    )
    await call.answer()
