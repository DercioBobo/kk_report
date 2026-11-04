from __future__ import unicode_literals

import frappe
import frappe.desk.query_report as core_query_report
from frappe import _


def set_user_language():
	"""Force the request language to the logged-in user's language.

	Translations are cached per request, so the cache must be reset after
	switching language.
	"""
	if frappe.session.user == "Guest":
		return

	from frappe.translate import get_user_lang

	lang = get_user_lang(frappe.session.user)
	if lang and lang != frappe.local.lang:
		frappe.local.lang = lang
		frappe.local.lang_full_dict = None


def _translate_column(col):
	if isinstance(col, dict):
		col = dict(col)
		if col.get("label"):
			col["label"] = _(col["label"])
		return col

	if isinstance(col, str):
		# Old-style column: "Label:Fieldtype/Options:Width"
		parts = col.split(":")
		parts[0] = _(parts[0])
		return ":".join(parts)

	return col


_STANDARD_HEADER_LABELS = {
	"Sr": "Nº",
	"Name": "ID",
	"Docstatus": "Document Status",
}


def _translate_header(label):
	if not isinstance(label, str):
		return label
	label = _STANDARD_HEADER_LABELS.get(label, label)
	return _(label)


@frappe.whitelist()
def export_list_view():
	"""List / Report View export (DocType list > Menu > Export) with headers in the user's language.

	Frappe v13 builds the header row from raw (English) field labels, plus "Sr".
	We translate the header row before the file is written.
	"""
	import frappe.desk.reportview as core_reportview
	import frappe.utils.xlsxutils as xlsxutils

	set_user_language()

	original_get_labels = core_reportview.get_labels
	original_make_xlsx = xlsxutils.make_xlsx
	had_local_make_xlsx = hasattr(core_reportview, "make_xlsx")

	def get_labels_translated(*args, **kwargs):
		return [_translate_header(l) for l in original_get_labels(*args, **kwargs)]

	def make_xlsx_translated(data, *args, **kwargs):
		if data and isinstance(data[0], (list, tuple)):
			data = [[_translate_header(h) for h in data[0]]] + list(data[1:])
		return original_make_xlsx(data, *args, **kwargs)

	core_reportview.get_labels = get_labels_translated
	xlsxutils.make_xlsx = make_xlsx_translated
	if had_local_make_xlsx:
		core_reportview.make_xlsx = make_xlsx_translated
	try:
		return core_reportview.export_query()
	finally:
		core_reportview.get_labels = original_get_labels
		xlsxutils.make_xlsx = original_make_xlsx
		if had_local_make_xlsx:
			core_reportview.make_xlsx = original_make_xlsx


@frappe.whitelist()
def export_query():
	"""Report Export (Menu > Export) with column headers in the user's language.

	The web UI translates column labels in the browser, but Frappe v13's export
	writes the raw (English) labels into the file. We translate them on the
	server before the file is built.
	"""
	set_user_language()

	original_run = core_query_report.run

	def run_translated(*args, **kwargs):
		result = original_run(*args, **kwargs)
		if isinstance(result, dict) and result.get("columns"):
			result["columns"] = [_translate_column(c) for c in result["columns"]]
		return result

	core_query_report.run = run_translated
	try:
		return core_query_report.export_query()
	finally:
		core_query_report.run = original_run
