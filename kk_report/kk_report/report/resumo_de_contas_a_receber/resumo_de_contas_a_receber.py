from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

AMOUNT_FIELDS = [
    "total_facturado",
    "total_pago",
    "total_em_divida",
    "range1",
    "range2",
    "range3",
    "range4",
    "range5",
    "total_devido",
]


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    def currency(fieldname, label, width=130):
        return {"fieldname": fieldname, "label": label, "fieldtype": "Currency", "width": width}

    return [
        {
            "fieldname": "customer",
            "label": _("Cliente"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 120,
        },
        {
            "fieldname": "customer_name",
            "label": _("Nome do Cliente"),
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "seguradora",
            "label": _("Seguradora"),
            "fieldtype": "Link",
            "options": "Seguradora",
            "width": 160,
        },
        currency("total_facturado", _("Total Facturado"), 140),
        currency("total_pago", _("Total Pago")),
        currency("total_em_divida", _("Total em Dívida"), 140),
        currency("range1", _("0-30")),
        currency("range2", _("31-60")),
        currency("range3", _("61-90")),
        currency("range4", _("91-120")),
        currency("range5", _("121-Acima")),
        currency("total_devido", _("Total Devido"), 140),
    ]


def get_data(filters):
    conditions, values = get_conditions(filters)

    # Ageing is measured from the posting date (or due date) up to the reference date
    age_field = "si.due_date" if filters.get("ageing_based_on") == "Due Date" else "si.posting_date"
    values.report_date = getdate(filters.get("report_date") or nowdate())

    rows = frappe.db.sql(
        """
        SELECT
            t.customer,
            MAX(t.customer_name) AS customer_name,
            t.seguradora,
            SUM(t.grand_total) AS total_facturado,
            SUM(t.grand_total - t.outstanding_amount) AS total_pago,
            SUM(t.outstanding_amount) AS total_em_divida,
            SUM(CASE WHEN t.age <= 30 THEN t.outstanding_amount ELSE 0 END) AS range1,
            SUM(CASE WHEN t.age BETWEEN 31 AND 60 THEN t.outstanding_amount ELSE 0 END) AS range2,
            SUM(CASE WHEN t.age BETWEEN 61 AND 90 THEN t.outstanding_amount ELSE 0 END) AS range3,
            SUM(CASE WHEN t.age BETWEEN 91 AND 120 THEN t.outstanding_amount ELSE 0 END) AS range4,
            SUM(CASE WHEN t.age > 120 THEN t.outstanding_amount ELSE 0 END) AS range5
        FROM (
            SELECT
                si.customer,
                si.customer_name,
                IFNULL(si.seguradora, '') AS seguradora,
                si.grand_total,
                si.outstanding_amount,
                DATEDIFF(%(report_date)s, IFNULL({age_field}, si.posting_date)) AS age
            FROM
                `tabSales Invoice` si
            WHERE
                si.docstatus = 1
                {conditions}
        ) t
        GROUP BY
            t.customer, t.seguradora
        {having}
        ORDER BY
            customer_name ASC,
            t.seguradora ASC
        """.format(
            age_field=age_field,
            conditions=conditions,
            having="HAVING SUM(t.outstanding_amount) != 0" if filters.get("only_outstanding") else "",
        ),
        values,
        as_dict=1,
    )

    data = []
    totals = frappe._dict({f: 0.0 for f in AMOUNT_FIELDS})

    for row in rows:
        row.total_devido = (
            flt(row.range1) + flt(row.range2) + flt(row.range3) + flt(row.range4) + flt(row.range5)
        )
        for f in AMOUNT_FIELDS:
            row[f] = flt(row[f], 2)
            totals[f] += row[f]
        data.append(row)

    # Totals row — bold: 1 renders it bold in the web UI
    if data:
        totals.update({"customer": _("Total"), "customer_name": "", "seguradora": "", "bold": 1})
        data.append(totals)

    return data


@frappe.whitelist()
def download_xlsx(filters=None):
    """Return a formatted Excel file with currency columns styled as #,##0.00."""
    import io

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.utils import get_column_letter

    from kk_report.overrides import set_user_language

    set_user_language()

    if isinstance(filters, str):
        filters = frappe.parse_json(filters)
    filters = frappe._dict(filters or {})

    columns = get_columns()
    data = get_data(filters)

    wb = Workbook()
    ws = wb.active
    ws.title = "Resumo Contas a Receber"

    ws.append([col["label"] for col in columns])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    currency_cols = [i + 1 for i, col in enumerate(columns) if col["fieldtype"] == "Currency"]

    for row in data:
        ws.append([row.get(col["fieldname"], "") for col in columns])

        current_row = ws.max_row
        is_total = bool(row.get("bold"))

        for col_idx in currency_cols:
            cell = ws.cell(row=current_row, column=col_idx)
            if isinstance(cell.value, (int, float)):
                cell.number_format = "#,##0.00"
            if is_total:
                cell.font = Font(bold=True)

        if is_total:
            ws.cell(row=current_row, column=1).font = Font(bold=True)

    for i, col in enumerate(columns, 1):
        ws.column_dimensions[get_column_letter(i)].width = max(col.get("width", 120) // 7, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    frappe.response["filename"] = "resumo_de_contas_a_receber.xlsx"
    frappe.response["filecontent"] = output.getvalue()
    frappe.response["type"] = "binary"


def get_conditions(filters):
    conditions = []
    values = frappe._dict()

    if filters.get("company"):
        conditions.append("si.company = %(company)s")
        values.company = filters.company

    if filters.get("date_from"):
        conditions.append("si.posting_date >= %(date_from)s")
        values.date_from = filters.date_from

    if filters.get("date_to"):
        conditions.append("si.posting_date <= %(date_to)s")
        values.date_to = filters.date_to

    if filters.get("customer"):
        conditions.append("si.customer = %(customer)s")
        values.customer = filters.customer

    if filters.get("seguradora"):
        conditions.append("si.seguradora = %(seguradora)s")
        values.seguradora = filters.seguradora

    cond_str = ("AND " + " AND ".join(conditions)) if conditions else ""
    return cond_str, values
