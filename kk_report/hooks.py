from . import __version__ as app_version

app_name = "kk_report"
app_title = "KK Report"
app_publisher = "KK"
app_description = "Custom Reports for ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = ""
app_license = "MIT"

# Fixtures — syncs report definitions on bench migrate
fixtures = [
    {
        "dt": "Report",
        "filters": [["name", "=", "Relatorio Mensal Seguradora"]],
    }
]
