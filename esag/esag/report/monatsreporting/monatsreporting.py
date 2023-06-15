# Copyright (c) 2023, Microsynth, libracore and contributors and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import date
from frappe.utils import cint

MONTHS = {
    1: _("Jan"),
    2: _("Feb"),
    3: _("Mar"),
    4: _("Apr"),
    5: _("Mai"),
    6: _("Jun"),
    7: _("Jul"),
    8: _("Aug"),
    9: _("Sep"),
    10: _("Oct"),
    11: _("Nov"),
    12: _("Dec"),
}

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):    
    columns = [
        {"label": _("Konto"), "fieldname": "account", "fieldtype": "Data", "width": 200}
    ]
    for m in range(1, 13):
        columns.append({
            "label": "IST {0} {1}".format(MONTHS[m], filters.fiscal_year), 
            "fieldname": "actual{0}".format(m), 
            "fieldtype": "Currency", 
            "options": "currency", 
            "width": 100
        })
        
    columns.append(
        {"label": "YTD", "fieldname": "ytd", "fieldtype": "Currency", "options": "currency", "width": 100}
    )
    columns.append(
        {"label": "Budget YTD", "fieldname": "budget_ytd", "fieldtype": "Currency", "options": "currency", "width": 100}
    )
    columns.append(
        {"label": "Abw. YTD", "fieldname": "dev_ytd", "fieldtype": "Currency", "options": "currency", "width": 100}
    )
    columns.append(
        {"label": "FC", "fieldname": "fc", "fieldtype": "Currency", "options": "currency", "width": 100}
    )
    columns.append(
        {"label": "Budget FY", "fieldname": "budget", "fieldtype": "Currency", "options": "currency", "width": 100}
    )
    columns.append(
        {"label": "", "fieldname": "blank", "fieldtype": "Data", "width": 20}
    )

    return columns

def get_data(filters):
    # prepare
    currency = frappe.get_cached_value("Company", filters.company, "default_currency")
    # prepare forcast:
    if cint(date.today().year) > cint(filters.fiscal_year):
        elapsed_month = 12          # the reporting year is complete
    else:
        elapsed_month = date.today().month - 1
    
    output = []
    group_count = 0
    total = {
        'account': "<b>TOTAL</b>",
        'ytd': 0,
        'fc': 0,
        'currency': currency,
        'budget': 0
    }
    for m in range (1, 13):
        key = 'actual{0}'.format(m)
        total[key] = 0
    accounts = get_accounts(filters)
    account_budget = get_budget_fy(filters.fiscal_year, filters.company)
    # create matrix
    for account in accounts:
        row = {
            'account': account,
            'ytd': 0,
            'fc': 0,
            'currency': currency,
            'budget': account_budget[account] if account in account_budget else 0
        }
        ytd = 0
        base = 0
        for m in range (1, 13):
            key = 'actual{0}'.format(m)
            row[key] = get_turnover(filters, m, account)
            ytd += row[key]
            if m <= elapsed_month:
                base += row[key]
        row['ytd'] = ytd
        row['fc'] = (12 * base / elapsed_month) if elapsed_month > 0 else 0
        row['currency'] = currency
        row['budget_ytd'] = (elapsed_month * row['budget'] / 12) if elapsed_month > 0 else 0
        row['dev_ytd'] = row['ytd'] - row['budget_ytd']

        # add each account
        output.append(row)
        
        total['ytd'] += row['ytd']
        total['fc'] += row['fc']
        total['budget'] += row['budget']
        for m in range (1, 13):
            key = 'actual{0}'.format(m)
            total[key] += row[key]
        
        group_count += 1
    
    output.append(total)
    
    return output

def get_accounts(filters):
    sql_query = """
       SELECT *, (`raw`.`credit` - `raw`.`debit`) AS `balance` 
       FROM
       (SELECT 
          `tabAccount`.`name` AS `account`, 
          IFNULL((SELECT 
             ROUND((SUM(`t3`.`debit`)), 2)
           FROM `tabGL Entry` AS `t3`
           WHERE 
             `t3`.`posting_date` LIKE "{year}-%"
            AND `t3`.`account` = `tabAccount`.`name`
          ), 0) AS `debit`,
          IFNULL((SELECT 
             ROUND((SUM(`t4`.`credit`)), 2)
           FROM `tabGL Entry` AS `t4`
           WHERE 
             `t4`.`posting_date`  LIKE "{year}-%"
            AND `t4`.`account` = `tabAccount`.`name`
          ), 0) AS `credit`
       FROM `tabAccount`
       WHERE 
         `tabAccount`.`is_group` = 0
         AND `tabAccount`.`report_type` = "Profit and Loss"
         AND `tabAccount`.`company` = "{company}"
       ) AS `raw`
       WHERE (`raw`.`debit` - `raw`.`credit`) != 0
       ;""".format(year=filters.fiscal_year, company=filters.company)
 
    # run query
    data = frappe.db.sql(sql_query, as_dict = True)
    accounts = []
    for a in data:
        accounts.append(a['account'])
    # extend with accounts from budget
    for k, v in (get_budget_fy(filters.fiscal_year, filters.company)).items():
        if k not in accounts:
            accounts.append(k)
    accounts.sort()
    return accounts
    
def get_turnover(filters, month, account):
    sql_query = """
        SELECT IFNULL((SUM(`credit`) - SUM(`debit`)), 0) AS `turnover`
        FROM `tabGL Entry`
        WHERE 
            `tabGL Entry`.`docstatus` = 1
            AND `tabGL Entry`.`company` = "{company}"
            AND `tabGL Entry`.`posting_date` LIKE "{year}-{month:02d}-%"
            AND `tabGL Entry`.`account` = "{account}"
        ;
    """.format(company=filters.company, year=filters.fiscal_year, month=month, 
        account=account)
    
    turnover = frappe.db.sql(sql_query, as_dict=True)[0]['turnover']
    
    return turnover

def get_budget_fy(year, company):
    data = frappe.db.sql("""SELECT 
            `tabBudget Account`.`account` AS  `account`,
            IFNULL(`tabBudget Account`.`budget_amount`, 0) AS `amount`
        FROM `tabBudget Account` 
        LEFT JOIN `tabBudget` ON `tabBudget Account`.`parent` = `tabBudget`.`name`
        WHERE 
          `tabBudget`.`fiscal_year` = "{year}"
          AND `tabBudget`.`docstatus` < 2
          AND `tabBudget`.`company` = "{company}";
            """.format(year=year, company=company), as_dict=True)
    account_budget = {}
    for d in data:
        account_budget[d['account']] = d['amount']
    return account_budget
