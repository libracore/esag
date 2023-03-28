# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data",  "width": 100},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group",  "width": 120},
        {"label": _("EAN Code"), "fieldname": "ean_code", "fieldtype": "Data",  "width": 100},
        {"label": _("Barcode"), "fieldname": "barcode", "fieldtype": "Data",  "width": 100},
        {"label": _("Item Status"), "fieldname": "item_status", "fieldtype": "Data",  "width": 80},
        # {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 80},
        {"label": _("Supplier name"), "fieldname": "supplier_name", "fieldtype": "Data",  "width": 100},
        {"label": _("EKP"), "fieldname": "ekp", "fieldtype": "Currency", "width": 80},
        {"label": _("VKP"), "fieldname": "vkp", "fieldtype": "Currency", "width": 80},
        {"label": _("OFT"), "fieldname": "oft", "fieldtype": "Currency", "width": 80},
        {"label": _("Sold Quantity"), "fieldname": "qty_sold", "fieldtype": "Float", "width": 80},
        {"label": _("Stock Quantity"), "fieldname": "qty_stock", "fieldtype": "Float", "width": 80},
        {"label": _("Revenue"), "fieldname": "revenue", "fieldtype": "Currency", "width": 80},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]

def get_data(filters):
        
    # fetch data
    sql_query = """
    SELECT 
        `tabItem`.`item_code` AS `item_code`,
        `tabItem`.`item_name` AS `item_name`,
        `tabItem`.`item_group` AS `item_group`,
        `tabItem`.`item_status` AS `item_status`,
        (SELECT `barcode` 
         FROM `tabItem Barcode` 
         WHERE `tabItem Barcode`.`parent` = `tabItem`.`name` 
           AND (`tabItem Barcode`.`barcode_type` IS NULL
            OR `tabItem Barcode`.`barcode_type` = "")
        ) AS `barcode`,
        (SELECT `supplier_name` 
         FROM `tabItem Default` 
         LEFT JOIN `tabSupplier` ON `tabSupplier`.`name` = `tabItem Default`.`default_supplier`
         WHERE `tabItem Default`.`parent` = `tabItem`.`name` 
        ) AS `supplier_name`,
        (SELECT `barcode` 
         FROM `tabItem Barcode` 
         WHERE `tabItem Barcode`.`parent` = `tabItem`.`name` 
           AND `tabItem Barcode`.`barcode_type` = "EAN"
        ) AS `ean_code`,
        (SELECT `price_list_rate` 
         FROM `tabItem Price` 
         WHERE `tabItem Price`.`item_code` = `tabItem`.`name` 
           AND `tabItem Price`.`price_list` = "Einkaufspreise"
        ) AS `ekp`,
        (SELECT `price_list_rate` 
         FROM `tabItem Price` 
         WHERE `tabItem Price`.`item_code` = `tabItem`.`name` 
           AND `tabItem Price`.`price_list` = "Verkaufspreise"
        ) AS `vkp`,
        (SELECT `price_list_rate` 
         FROM `tabItem Price` 
         WHERE `tabItem Price`.`item_code` = `tabItem`.`name` 
           AND `tabItem Price`.`price_list` = "OFT Preise"
        ) AS `oft`,
        (SELECT IFNULL(SUM(`qty` ), 0)
         FROM `tabSales Invoice Item` AS `sii1`
         LEFT JOIN `tabSales Invoice` AS `si1` ON `si1`.`name` = `sii1`.`parent`
         WHERE 
           `si1`.`docstatus` = 1
           AND `sii1`.`item_code` = `tabItem`.`name` 
           AND `si1`.`posting_date` BETWEEN "{from_date}" AND "{to_date}"
        ) AS `qty_sold`,
        (SELECT SUM(`base_net_amount` )
         FROM `tabSales Invoice Item` AS `sii2`
         LEFT JOIN `tabSales Invoice` AS `si2` ON `si2`.`name` = `sii2`.`parent`
         WHERE 
           `si2`.`docstatus` = 1
           AND `sii2`.`item_code` = `tabItem`.`name` 
           AND `si2`.`posting_date` BETWEEN "{from_date}" AND "{to_date}"
        ) AS `revenue`,
        (SELECT IFNULL(SUM(`actual_qty`), 0)
         FROM `tabBin` 
         WHERE 
           `tabBin`.`item_code` = `tabItem`.`name` 
        ) AS `qty_stock`
    FROM `tabItem`
    WHERE
        `tabItem`.`disabled` = 0
        AND `tabItem`.`is_sales_item` = 1;
    """.format(from_date=filters['from_date'], to_date=filters['to_date'])

    data = frappe.db.sql(sql_query, as_dict=True)
    return data
