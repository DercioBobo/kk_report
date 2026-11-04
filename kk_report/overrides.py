from __future__ import unicode_literals

import frappe
from frappe.desk.query_report import export_query as _core_export_query


def set_user_language():
	"""Force the request language to the logged-in user's language.

	Downloads opened via ``open_url_post`` are plain form POSTs, so the request
	language can fall back to the browser / system default (English) instead of
	the language set on the User. Translations are also cached per request, so
	the cache must be reset after switching language.
	"""
	if frappe.session.user == "Guest":
		return

	from frappe.translate import get_user_lang

	lang = get_user_lang(frappe.session.user)
	if lang and lang != frappe.local.lang:
		frappe.local.lang = lang
		frappe.local.lang_full_dict = None


@frappe.whitelist()
def export_query():
	"""Wrapper around the standard report Export (Menu > Export) that uses the user's language."""
	set_user_language()
	return _core_export_query()
