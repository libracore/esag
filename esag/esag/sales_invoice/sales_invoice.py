# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def check_gutschein(sinv, event):
    if sinv.is_pos and sinv.pos_profile and not sinv.is_return:
        gutschein_item = frappe.db.get_value("POS Profile", sinv.pos_profile, 'gutschein_artikel') or None
        franken_pro_stuck = frappe.db.get_value("POS Profile", sinv.pos_profile, 'franken_pro_stuck') or 1
        for item in sinv.items:
            if item.item_code == gutschein_item:
                create_gutschein(sinv.name, item.qty * franken_pro_stuck)
        
        if sinv.gutschein and sinv.gutschein_betrag:
            recalc_gutschein(sinv.gutschein, sinv.gutschein_betrag)

def create_gutschein(sinv, amount):
    if not frappe.db.exists("POS Gutschein", {"sales_invoice": sinv}):
        new_gutschein = frappe.get_doc({
            "doctype": "POS Gutschein",
            "sales_invoice": sinv,
            "betrag": amount,
            "bezug": 0,
            "verfuegbar": amount
        })
        new_gutschein.insert()

def recalc_gutschein(gutschein, amount):
    if frappe.db.exists("POS Gutschein", gutschein):
        voucher = frappe.get_doc("POS Gutschein", gutschein)
        voucher.bezug += amount
        voucher.verfuegbar -= amount
        voucher.save()