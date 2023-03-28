# Copyright (c) 2022-2023, libracore and Contributors
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

@frappe.whitelist()
def get_next_barcode():
    last = frappe.db.sql("""
        SELECT `barcode`
        FROM `tabItem Barcode`
        WHERE LENGTH(`barcode`) = 14
        ORDER BY `barcode` DESC
        LIMIT 1
    """, as_dict=True)
    if len(last) > 0:
        last_id = int(last[0]['barcode'])
    else:
        last_id = 0
    return "{0:014d}".format(last_id + 1)

"""
Calculate the intermediate price from two price lists and write to target price list
"""
@frappe.whitelist()
def intermediate_price(item_code, ek_price_list, vk_price_list, target_price_list):
    # fetch prices
    prices = frappe.db.sql("""
        SELECT 
        `tabItem`.`item_code` AS `item_code`,
        IFNULL((SELECT `price_list_rate` 
         FROM `tabItem Price` 
         WHERE `tabItem Price`.`item_code` = `tabItem`.`name` 
           AND `tabItem Price`.`price_list` = "{ekp}"
        ), 0) AS `ekp`,
        IFNULL((SELECT `price_list_rate` 
         FROM `tabItem Price` 
         WHERE `tabItem Price`.`item_code` = `tabItem`.`name` 
           AND `tabItem Price`.`price_list` = "{vkp}"
        ), 0) AS `vkp`
    FROM `tabItem`;
    """, as_dict=True)
    intermediate = (prices[0]['ekp'] + prices[0]['vkp'])/2
    # check if the target price exists
    target_prices = frappe.get_all("Item Price", 
        filters={'item_code': item_code, 'price_list': target_price_list}, 
        fields=['name']
    )
    if len(target_prices) > 0:
        # update
        doc = frappe.get_doc("Item Price", target_prices[0]['name'])
        doc.price_list_rate = intermediate
        doc.save()
    else:
        # create
        doc = frappe.get_doc({
            'doctype': 'Item Price',
            'item_code': item_code,
            'price_list': target_price_list,
            'price_list_rate': intermediate
        })
        doc.insert()
    frappe.db.commit()
    return
    
