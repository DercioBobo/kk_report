from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "posting_date",
            "label": _("Data"),
            "fieldtype": "Data",
            "width": 110,
        },
        {
            "fieldname": "name",
            "label": _("Nº Factura"),
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 170,
        },
        {
            "fieldname": "membro_apolice",
            "label": _("Nº Membro"),
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "net_total",
            "label": _("Valor (MZN)"),
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "fieldname": "total_taxes_and_charges",
            "label": _("IVA (MZN)"),
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "fieldname": "grand_total",
            "label": _("Total (MZN)"),
            "fieldtype": "Currency",
            "width": 150,
        },
    ]


def get_data(filters):
    conditions, values = get_conditions(filters)

    rows = frappe.db.sql(
        """
        SELECT
            si.posting_date,
            si.name,
            si.membro_apolice,
            si.net_total,
            si.total_taxes_and_charges,
            si.grand_total
        FROM
            `tabSales Invoice` si
        WHERE
            si.docstatus = 1
            {conditions}
        ORDER BY
            si.posting_date ASC,
            si.name ASC
        """.format(
            conditions=conditions
        ),
        values,
        as_dict=1,
    )

    data = []
    total_net = 0.0
    total_tax = 0.0
    total_grand = 0.0

    for row in rows:
        # Format date as dd/mm/yyyy — preserved as-is in all export formats
        if row.posting_date:
            row.posting_date = getdate(row.posting_date).strftime("%d/%m/%Y")

        total_net += flt(row.net_total)
        total_tax += flt(row.total_taxes_and_charges)
        total_grand += flt(row.grand_total)

        data.append(row)

    # Totals row — bold: 1 renders it bold in the web UI
    if data:
        data.append(
            {
                "posting_date": _("Total"),
                "name": "",
                "membro_apolice": "",
                "net_total": total_net,
                "total_taxes_and_charges": total_tax,
                "grand_total": total_grand,
                "bold": 1,
            }
        )

    return data


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

    if filters.get("seguradora"):
        conditions.append("si.seguradora = %(seguradora)s")
        values.seguradora = filters.seguradora

    if filters.get("status"):
        conditions.append("si.status = %(status)s")
        values.status = filters.status

    cond_str = ("AND " + " AND ".join(conditions)) if conditions else ""
    return cond_str, values
