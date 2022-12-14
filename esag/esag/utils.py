# Copyright (c) 2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from datetime import date
from frappe.utils import cint

@frappe.whitelist()
def get_next_item_code(customer_order=False):
    if cint(customer_order):
        # mask KA_YYYY_###
        current_year = date.today().year
        mask="KA_{0}_".format(current_year)
        last = frappe.db.sql("""
            SELECT `item_code`
            FROM `tabItem`
            WHERE `item_code` LIKE "{mask}%"
              AND LENGTH(`item_code`) = 11
            ORDER BY `item_code` DESC
            LIMIT 1
        """.format(mask=mask), as_dict=True)
        if len(last) > 0:
            last_id = int(last[0]['item_code'][-3:])
        else:
            last_id = 0
        return "{0}{1:03d}".format(mask, last_id + 1)
    else:
        # mask ETH_#####
        last = frappe.db.sql("""
            SELECT `item_code`
            FROM `tabItem`
            WHERE `item_code` LIKE "ETH_%"
              AND LENGTH(`item_code`) = 9
            ORDER BY `item_code` DESC
            LIMIT 1
        """, as_dict=True)
        if len(last) > 0:
            last_id = int(last[0]['item_code'][-5:])
        else:
            last_id = 0
        return "ETH_{0:05d}".format(last_id + 1)
