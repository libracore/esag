from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
        {
            "label": _("Stock"),
            "icon": "fa fa-users",
            "items": [
                    {
                        "type": "doctype",
                        "name": "Item",
                        "label": _("Item")
                    },
                    {
                        "type": "doctype",
                        "name": "Translation",
                        "label": _("Translation")
                    },
                    {
                        "type": "doctype",
                        "name": "BOM",
                        "label": _("BOM")
                    },
                    {
                        "type": "doctype",
                        "name": "Item Price",
                        "label": _("Item Price")
                    },
                    {
                        "type": "doctype",
                        "name": "Purchase Receipt",
                        "label": _("Purchase Receipt")
                    },
                    {
                        "type": "doctype",
                        "name": "Delivery Note",
                        "label": _("Delivery Note")
                    },
                    {
                        "type": "doctype",
                        "name": "Stock Entry",
                        "label": _("Stock Entry")
                    },
                    {
                        "type": "page",
                        "name": "stock-balance",
                        "label": _("Stock Summary"),
                        "dependencies": ["Item"],
                    },
                    {
                        "type": "report",
                        "is_query_report": True,
                        "name": "Stock Balance",
                        "doctype": "Stock Ledger Entry",
                        "onboard": 1,
                        "dependencies": ["Item"],
                    }
            ]
        },
        {
            "label": _("Selling"),
            "icon": "fa fa-users",
            "items": [
                    {
                        "type": "doctype",
                        "name": "Customer",
                        "label": _("Customer")
                    },
                    {
                        "type": "doctype",
                        "name": "Quotation",
                        "label": _("Quotation")
                    },
                    {
                        "type": "doctype",
                        "name": "Sales Order",
                        "label": _("Sales Order")
                    },
                    {
                        "type": "doctype",
                        "name": "Delivery Note",
                        "label": _("Delivery Note")
                    },
                    {
                        "type": "doctype",
                        "name": "Sales Invoice",
                        "label": _("Sales Invoice")
                    }
            ]
        },
        {
            "label": _("Buying"),
            "icon": "fa fa-users",
            "items": [
                    {
                        "type": "doctype",
                        "name": "Supplier",
                        "label": _("Supplier")
                    },
                    {
                        "type": "doctype",
                        "name": "Request for Quotation",
                        "label": _("Request for Quotation")
                    },
                    {
                        "type": "doctype",
                        "name": "Supplier Quotation",
                        "label": _("Supplier Quotation")
                    },
                    {
                        "type": "doctype",
                        "name": "Purchase Order",
                        "label": _("Purchase Order")
                    },
                    {
                        "type": "doctype",
                        "name": "Purchase Receipt",
                        "label": _("Purchase Receipt")
                    },
                    {
                        "type": "doctype",
                        "name": "Purchase Invoice",
                        "label": _("Purchase Invoice")
                    }
            ]
        },
        {
            "label": _("Finance"),
            "icon": "fa fa-users",
            "items": [
                    {
                        "type": "doctype",
                        "name": "Sales Invoice",
                        "label": _("Sales Inoice")
                    },
                    {
                        "type": "report",
                        "name": "Accounts Receivable",
                        "label": _("Accounts Receivable"),
                        "doctype": "Sales Invoice",
                        "is_query_report": True
                    },
                    {
                        "type": "doctype",
                        "name": "Purchase Invoice",
                        "label": _("Purchase Inoice")
                    },
                    {
                        "type": "report",
                        "name": "Accounts Payable",
                        "label": _("Accounts Payable"),
                        "doctype": "Purchase Invoice",
                        "is_query_report": True
                    },
                    {
                        "type": "report",
                        "name": "General Ledger",
                        "label": _("General Ledger"),
                        "doctype": "GL Entry",
                        "is_query_report": True
                    },
                    {
                        "type": "doctype",
                        "name": "Payment Proposal",
                        "label": _("Payment Proposal")
                    },
                    {
                       "type": "page",
                       "name": "bank_wizard",
                       "label": _("Bank Wizard"),
                       "description": _("Bank Wizard")
                    },
                    {
                        "type": "doctype",
                        "name": "Payment Entry",
                        "label": _("Payment Entry")
                    },
                    {
                        "type": "doctype",
                        "name": "Journal Entry",
                        "label": _("Journal Entry")
                    },
                    {
                        "type": "doctype",
                        "name": "Payment Reminder",
                        "label": _("Payment Reminder")
                    },
                    {
                        "type": "report",
                        "name": "Balance Sheet",
                        "label": _("Balance Sheet"),
                        "doctype": "GL Entry",
                        "is_query_report": True
                    },
                    {
                        "type": "report",
                        "name": "Profit and Loss Statement",
                        "label": _("Profit and Loss Statement"),
                        "doctype": "GL Entry",
                        "is_query_report": True
                    },
                    {
                        "type": "report",
                        "name": "Account Sheets",
                        "label": _("Account Sheets"),
                        "doctype": "GL Entry",
                        "is_query_report": True
                    },
                    {
                       "type": "doctype",
                       "name": "VAT Declaration",
                       "label": _("VAT Declaration"),
                       "description": _("VAT Declaration")
                    },
                    {
                        "type": "report",
                        "name": "Kontrolle MwSt",
                        "label": _("Kontrolle MwSt"),
                        "doctype": "Sales Invoice",
                        "is_query_report": True
                    }
            ]
        },
        {
            "label": _("HR"),
            "icon": "fa fa-users",
            "items": [
                    {
                        "type": "doctype",
                        "name": "Employee",
                        "label": _("Employee")
                    },
                    {
                        "type": "doctype",
                        "name": "Salary Structure Assignment",
                        "label": _("Salary Structure Assignment")
                    },
                    {
                        "type": "doctype",
                        "name": "Timesheet",
                        "label": _("Timesheet")
                    },
                    {
                        "type": "doctype",
                        "name": "Payroll Entry",
                        "label": _("Payroll Entry")
                    },
                    {
                        "type": "doctype",
                        "name": "Salary Component",
                        "label": _("Salary Component")
                    },
                    {
                        "type": "doctype",
                        "name": "Salary Structure",
                        "label": _("Salary Structure")
                    },
                    {
                        "type": "doctype",
                        "name": "Expense Claim",
                        "label": _("Expense Claim")
                    },
                    {
                       "type": "doctype",
                       "name": "Salary Certificate",
                       "label": _("Salary Certificate"),
                       "description": _("Salary Certificate")
                    },
                    {
                        "type": "report",
                        "name": "Annual Salary Sheet",
                        "label": _("Annual Salary Sheet"),
                        "doctype": "Salary Slip",
                        "is_query_report": True
                    }
            ]
        },
        {
            "label": _("Zeiterfassung"),
            "icon": "fa fa-users",
            "items": [
                    {
                        "type": "doctype",
                        "name": "Timesheet",
                        "label": _("Timesheet")
                    },
                    {
                        "type": "report",
                        "name": "Worktime Overview",
                        "label": _("Worktime Overview"),
                        "doctype": "Timesheet",
                        "is_query_report": True
                    },
                    {
                        "type": "report",
                        "name": "Monthly Worktime",
                        "label": _("Monthly Worktime"),
                        "doctype": "Timesheet",
                        "is_query_report": True
                    }
            ]
        },
        {
            "label": _("Reporting"),
            "icon": "fa fa-users",
            "items": [
                {
                    "type": "report",
                    "is_query_report": True,
                    "name": "Sales Analytics",
                    "doctype": "Sales Order"
                },
                {
                    "type": "report",
                    "is_query_report": True,
                    "name": "Purchase Analytics",
                    "reference_doctype": "Purchase Order"
                }
            ]
        }
    ]
