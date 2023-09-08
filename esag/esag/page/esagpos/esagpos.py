# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.nestedset import get_root_of
from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups
from frappe import auth
from frappe.utils.password import get_decrypted_password, decrypt, encrypt

@frappe.whitelist()
def get_items(start, page_length, price_list, item_group, search_value="", pos_profile=None):
    data = dict()
    warehouse = ""
    display_items_in_stock = 0

    if pos_profile:
        warehouse, display_items_in_stock = frappe.db.get_value('POS Profile', pos_profile, ['warehouse', 'display_items_in_stock'])

    if not frappe.db.exists('Item Group', item_group):
        item_group = get_root_of('Item Group')

    if search_value:
        data = search_serial_or_batch_or_barcode_number(search_value)

    item_code = data.get("item_code") if data.get("item_code") else search_value
    serial_no = data.get("serial_no") if data.get("serial_no") else ""
    batch_no = data.get("batch_no") if data.get("batch_no") else ""
    barcode = data.get("barcode") if data.get("barcode") else ""

    condition = get_conditions(item_code, serial_no, batch_no, barcode)

    if pos_profile:
        condition += get_item_group_condition(pos_profile)

    lft, rgt = frappe.db.get_value('Item Group', item_group, ['lft', 'rgt'])
    # locate function is used to sort by closest match from the beginning of the value


    result = []

    items_data = frappe.db.sql(""" SELECT name as item_code,
            item_name, image as item_image, idx as idx,is_stock_item
        FROM
            `tabItem`
        WHERE
            disabled = 0 and has_variants = 0 and is_sales_item = 1
            and item_group in (select name from `tabItem Group` where lft >= {lft} and rgt <= {rgt})
            and {condition} order by idx desc limit {start}, {page_length}"""
        .format(
            start=start, page_length=page_length,
            lft=lft, rgt=rgt,
            condition=condition
        ), as_dict=1)

    if items_data:
        items = [d.item_code for d in items_data]
        item_prices_data = frappe.get_all("Item Price",
            fields = ["item_code", "price_list_rate", "currency"],
            filters = {'price_list': price_list, 'item_code': ['in', items]})

        item_prices, bin_data = {}, {}
        for d in item_prices_data:
            item_prices[d.item_code] = d


        if display_items_in_stock:
            filters = {'actual_qty': [">", 0], 'item_code': ['in', items]}

            if warehouse:
                filters['warehouse'] = warehouse

            bin_data = frappe._dict(
                frappe.get_all("Bin", fields = ["item_code", "sum(actual_qty) as actual_qty"],
                filters = filters, group_by = "item_code")
            )

        for item in items_data:
            row = {}

            row.update(item)
            item_price = item_prices.get(item.item_code) or {}
            
            # get Brutto-Preis
            gross_price = None
            if item_price.get('price_list_rate'):
                item_base = frappe.get_doc("Item", item.item_code)
                if len(item_base.taxes) > 0:
                    item_tax_template = frappe.get_doc("Item Tax Template", item_base.taxes[0].item_tax_template)
                    if len(item_tax_template.taxes) > 0:
                        tax_rate = 100 + item_tax_template.taxes[0].tax_rate
                        gross_price = (item_price.get('price_list_rate') / 100) * tax_rate
            
            row.update({
                'price_list_rate': item_price.get('price_list_rate'),
                'currency': item_price.get('currency'),
                'actual_qty': bin_data.get('actual_qty'),
                'gross_price': gross_price
            })

            result.append(row)

    res = {
        'items': result
    }

    if serial_no:
        res.update({
            'serial_no': serial_no
        })

    if batch_no:
        res.update({
            'batch_no': batch_no
        })

    if barcode:
        res.update({
            'barcode': barcode
        })

    return res

def get_conditions(item_code, serial_no, batch_no, barcode):
    if serial_no or batch_no or barcode:
        return "name = {0}".format(frappe.db.escape(item_code))

    return """(name like {item_code}
        or item_name like {item_code})""".format(item_code = frappe.db.escape('%' + item_code + '%'))

def get_item_group_condition(pos_profile):
    cond = "and 1=1"
    item_groups = get_item_groups(pos_profile)
    if item_groups:
        cond = "and item_group in (%s)"%(', '.join(['%s']*len(item_groups)))

    return cond % tuple(item_groups)

@frappe.whitelist()
def search_serial_or_batch_or_barcode_number(search_value):
    # search barcode no
    barcode_data = frappe.db.get_value('Item Barcode', {'barcode': search_value}, ['barcode', 'parent as item_code'], as_dict=True)
    if barcode_data:
        return barcode_data

    # search serial no
    serial_no_data = frappe.db.get_value('Serial No', search_value, ['name as serial_no', 'item_code'], as_dict=True)
    if serial_no_data:
        return serial_no_data

    # search batch no
    batch_no_data = frappe.db.get_value('Batch', search_value, ['name as batch_no', 'item as item_code'], as_dict=True)
    if batch_no_data:
        return batch_no_data

    return {}

@frappe.whitelist()
def esag_pos_login(encrypted_hash):
    try:
        decrypted_hash = decrypt(encrypted_hash)
        user = decrypted_hash.split("|")[0]
        pwd = decrypted_hash.split("|")[1]
        try:
            login_manager = frappe.auth.LoginManager()
            login_manager.authenticate(user=user, pwd=pwd)
            login_manager.post_login()
            return True
        except frappe.exceptions.AuthenticationError:
            frappe.clear_messages()
            return False
    except:
        frappe.clear_messages()
        return False

@frappe.whitelist()
def esag_pos_logout(posprofiluser, posprofil):
    pwd = get_decrypted_password('POS Profile', posprofil)
    try:
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=posprofiluser, pwd=pwd)
        login_manager.post_login()
        return True
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        return False

@frappe.whitelist()
def get_esag_pos_qr(user, pwd):
    str_to_encrypt = "{0}|{1}".format(user, pwd)
    return encrypt(str_to_encrypt)
