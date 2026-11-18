// Copyright (c) 2024, KK and contributors
// For license information, please see license.txt

frappe.query_reports["Resumo de Contas a Receber"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Empresa"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_default("company"),
			reqd: 0,
		},
		{
			fieldname: "report_date",
			label: __("Data de Referência"),
			fieldtype: "Date",
			default: frappe.datetime.now_date(),
			reqd: 1,
		},
		{
			fieldname: "ageing_based_on",
			label: __("Antiguidade com Base em"),
			fieldtype: "Select",
			options: "Posting Date\nDue Date",
			default: "Posting Date",
		},
		{
			fieldname: "date_from",
			label: __("Facturas De"),
			fieldtype: "Date",
			reqd: 0,
		},
		{
			fieldname: "date_to",
			label: __("Facturas Até"),
			fieldtype: "Date",
			reqd: 0,
		},
		{
			fieldname: "customer",
			label: __("Cliente"),
			fieldtype: "Link",
			options: "Customer",
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
			fieldname: "only_outstanding",
			label: __("Apenas com Dívida"),
			fieldtype: "Check",
			default: 0,
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
				"/api/method/kk_report.kk_report.report.resumo_de_contas_a_receber.resumo_de_contas_a_receber.download_xlsx",
				{ filters: JSON.stringify(filters) }
			);
		});
	},
};
