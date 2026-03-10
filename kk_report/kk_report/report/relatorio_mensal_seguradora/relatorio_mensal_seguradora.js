// Copyright (c) 2024, KK and contributors
// For license information, please see license.txt

frappe.query_reports["Relatorio Mensal Seguradora"] = {
	filters: [
		{
			fieldname: "date_from",
			label: __("Data De"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 0,
		},
		{
			fieldname: "date_to",
			label: __("Data Até"),
			fieldtype: "Date",
			default: frappe.datetime.now_date(),
			reqd: 0,
		},
		{
			fieldname: "company",
			label: __("Empresa"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_default("company"),
			reqd: 0,
		},
		{
			fieldname: "seguradora",
			label: __("Seguradora"),
			fieldtype: "Link",
			options: "Seguradora",
			reqd: 0,
		},
		{
			fieldname: "status",
			label: __("Estado"),
			fieldtype: "Select",
			options: "\nPaid\nUnpaid\nOverdue\nReturn\nCredit Note Issued",
			reqd: 0,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		// Bold the totals row
		value = default_formatter(value, row, column, data);
		if (data && data.bold) {
			value = "<strong>" + value + "</strong>";
		}
		return value;
	},

	onload: function (report) {
		report.page.add_inner_button(__("Exportar Excel"), function () {
			const filters = report.get_values();
			open_url_post(
				"/api/method/kk_report.kk_report.report.relatorio_mensal_seguradora.relatorio_mensal_seguradora.download_xlsx",
				{ filters: JSON.stringify(filters) }
			);
		});
	},
};
