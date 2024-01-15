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
from escpos import *
from frappe.utils.data import get_datetime
import json
from frappe.utils import flt

@frappe.whitelist()
def receipt_print(sinv=None, test_print=False):
    try:
        if test_print:
            # connect printer
            printer_ip = test_print
            if not printer_ip:
                return False
            try:
                p = connect_printer(printer_ip)
                p.charcode('USA')
                p.set(align='left')
                p.text("------------------------------------------------\n")
                p.set(align='center')
                p.text("Testdruck erfolgreich\n")
                p.set(align='left')
                p.text("------------------------------------------------")
                p.cut()
                return 1
            except Exception as err:
                frappe.log_error("{0}".format(err), "connect printer failed")
                return False
        
        if not sinv:
            # no sinv no receipt
            return
        
        sinv = frappe.get_doc("Sales Invoice", sinv)
        
        if not sinv.pos_profile:
            # no pos profile no receipt
            return
        
        if sinv.is_return == 1:
            frappe.throw("Retouren können nicht auf dem Thermo Printer gedruckt werden.")
        
        # connect printer
        printer_ip = frappe.db.get_value("POS Profile", sinv.pos_profile, 'receipt_printer_ip')
        if not printer_ip:
            return
        try:
            p = connect_printer(printer_ip)
        except Exception as err:
            frappe.log_error("{0}".format(err), "connect printer failed")
            return
        
        itemised_tax = _get_itemised_tax(sinv)
        mwst_dict = {}
        mwst_dict_keys = []
        mwst_code_loop = 1
        mwst_code_dict = {}
        items = []
        
        for sinv_item in sinv.items:
            item_base = frappe.get_doc("Item", sinv_item.item_code)
            tax_amount = 0
            if itemised_tax:
                if sinv_item.item_code in itemised_tax:
                    if sinv_item.item_tax_template in itemised_tax[sinv_item.item_code]:
                        tax_amount += itemised_tax[sinv_item.item_code][sinv_item.item_tax_template]['tax_amount']
                        
                        mwst_tax_amount = itemised_tax[sinv_item.item_code][sinv_item.item_tax_template]['tax_amount']
                        mwst_total_amount = sinv_item.amount + mwst_tax_amount
                        tax_rate = itemised_tax[sinv_item.item_code][sinv_item.item_tax_template]['tax_rate']
                        mwst_dict_keys.append(tax_rate)
                        if tax_rate in mwst_dict:
                            mwst_dict[tax_rate]['total'] += mwst_total_amount
                            mwst_dict[tax_rate]['mwst'] += mwst_tax_amount
                        else:
                            mwst_dict[tax_rate] = {
                                'total': mwst_total_amount,
                                'mwst': mwst_tax_amount,
                                'mwst_code': mwst_code_loop
                            }
                            mwst_code_dict[sinv_item.item_tax_template] = mwst_code_loop
                            mwst_code_loop += 1
            
            discount = False
            if sinv_item.discount_amount > 0 or sinv_item.discount_percentage > 0:
                if sinv_item.discount_percentage > 0:
                    discount = str(sinv_item.discount_percentage) + "%"
                else:
                    discount = "CHF " + str(frappe.utils.fmt_money(sinv_item.discount_amount))
            
            items.append({
                'item_name': sinv_item.item_name,
                'qty': int(sinv_item.qty),
                'rate': sinv_item.rate + (tax_amount / sinv_item.qty),
                'total': sinv_item.amount + tax_amount,
                'garantie': True if item_base.has_warranty else False,
                'garantie_dauer': item_base.warranty,
                'mwst_code': mwst_code_dict[sinv_item.item_tax_template],
                'discount': discount
            })
        
        # default codepage
        p.charcode('USA')
        
        # Header
        p.set(align='center')
        p.image('/home/frappe/frappe-bench/apps/esag/esag/esag/page/esagpos/ETH_Store_Logo.png')
        p.set(align='left')
        p.text("------------------------------------------------\n")
        p.set(align='center')
        p.text("ETH Store AG\nMerchandise Store\nClausiusstrasse 2\n8006 Zürich\nTel. +41 44 633 83 38\n")
        p.qr("https://www.eth-store.ch/", size=4)
        p.set(align='left')
        p.text("------------------------------------------------\n\n")
        
        # Items Table
        p.set(text_type="B")
        p.text("Artikel              Menge   Preis    Total    C\n")
        p.set(text_type="NORMAL")
        
        
        
        for item_dict in items:
            # Artikelname
            item = item_dict['item_name']
            if len(item) > 19:
                item = item[:19] + "  "
            else:
                item = item.ljust(21, " ")
            
            # Artikelmenge
            qty = str(item_dict['qty'])
            if len(qty) > 7:
                qty = qty[:7] + " "
            else:
                qty = qty.ljust(8, " ")
            
            # Artikelpreis
            rate = str(frappe.utils.fmt_money(item_dict['rate']))
            if len(rate) > 8:
                rate = rate[:8] + " "
            else:
                rate = rate.ljust(9, " ")
            
            # Positions Total
            total = str(frappe.utils.fmt_money(item_dict['total']))
            if len(total) > 8:
                total = total[:8] + " "
            else:
                total = total.ljust(9, " ")
            
            # MWST Code
            mwst_code = str(item_dict['mwst_code'])
            
            p.text("{0}{1}{2}{3}{4}\n".format(item, qty, rate, total, mwst_code))
            
            # Artikelspezifischer Rabatt
            discount = item_dict['discount']
            if discount:
                p.text("               Inkl. Rabatt ({0})\n".format(discount))
            
            # Artikelspezifische Garantie
            garantie = item_dict['garantie']
            if garantie:
                garantie_dauer = item_dict['garantie_dauer']
                p.text("{0} Garantie\n\n".format(garantie_dauer))
            else:
                p.text("\n")
        

        # Rückgabe Items Table
        if sinv.gegengerechnete_gutschrift:
            p.set(text_type="B")
            p.text("Rücknahmen\n")
            p.text("Artikel                                    Menge\n")
            p.set(text_type="NORMAL")

            return_sinv = frappe.get_doc("Sales Invoice", sinv.gegengerechnete_gutschrift)
            for return_item in return_sinv.items:
                if len(return_item.item_name) > 38:
                    return_item_txt = return_item.item_name[:42] + "  "
                else:
                    return_item_txt = return_item.item_name.ljust(44, " ")
                return_item_qty = str(return_item.qty)
                p.text("{0}{1}\n".format(return_item_txt, return_item_qty))
            p.text("\n")
            total_ruecknahme_amount = str(frappe.utils.fmt_money(return_sinv.paid_amount))
            total_ruecknahme_string = "Abzüglich Rücknahmen CHF"
            if (len(total_ruecknahme_amount) + len(total_ruecknahme_string)) < 43:
                adjust = 43 - len(total_ruecknahme_amount)
                total_ruecknahme_string = total_ruecknahme_string.ljust(adjust, " ")
            p.text("{0}{1}\n".format(total_ruecknahme_string, total_ruecknahme_amount))
        
        # Rechnungsübergreifender Rabatt
        if sinv.discount_amount > 0:
            total_amount = str(frappe.utils.fmt_money(sinv.discount_amount))
            total_string = "Abzüglich Rabatt CHF"
            
            if (len(total_amount) + len(total_string)) < 43:
                adjust = 43 - len(total_amount)
                total_string = total_string.ljust(adjust, " ")
            
            p.text("{0}{1}\n".format(total_string, total_amount))
        
        # Total und Rundungsdifferenz
        if sinv.rounding_adjustment > 0:
            # Total ungerundet
            total_amount = str(frappe.utils.fmt_money(sinv.grand_total))
            total_string = "Zwischentotal CHF"
            
            if (len(total_amount) + len(total_string)) < 43:
                adjust = 43 - len(total_amount)
                total_string = total_string.ljust(adjust, " ")
            
            p.text("{0}{1}\n".format(total_string, total_amount))
            
            # Rundungsdifferenz
            total_amount = str(frappe.utils.fmt_money(sinv.rounding_adjustment))
            total_string = "Rundungsdifferenz CHF"
            
            if (len(total_amount) + len(total_string)) < 43:
                adjust = 43 - len(total_amount)
                total_string = total_string.ljust(adjust, " ")
            
            p.text("{0}{1}\n".format(total_string, total_amount))
        
        # Total gerundet
        if sinv.gegengerechnete_gutschrift:
            total_amount = str(frappe.utils.fmt_money(sinv.rounded_total - return_sinv.paid_amount))
        else:
            total_amount = str(frappe.utils.fmt_money(sinv.rounded_total))
        total_string = "TOTAL CHF"
        
        if (len(total_amount) + len(total_string)) < 43:
            adjust = 43 - len(total_amount)
            total_string = total_string.ljust(adjust, " ")
        
        p.set(text_type="B")
        p.text("{0}{1}\n".format(total_string, total_amount))
        p.set(text_type="NORMAL")
        p.text("------------------------------------------------\n")
        
        # Zahlungsdetails
        for payment_method in sinv.payments:
            pm = str(payment_method.mode_of_payment).ljust(21, " ")
            pm_amount = str(frappe.utils.fmt_money(payment_method.amount))
            p.text("{0}{1}\n".format(pm, pm_amount))
        if sinv.eft_details:
            p.text("{0}\n".format(sinv.eft_details))
        p.text("------------------------------------------------\n")
        
        # MWST
        p.text("ETH Store AG,        CHE-264.182.531 MWST\n")
        if len(mwst_dict_keys) > 0:
            p.text("Code    MWST         Total     MWST\n")
        printed_mwst_codes = []
        for mwst_satz in mwst_dict_keys:
            mwst_code = str(mwst_dict[mwst_satz]['mwst_code']).ljust(8, " ")
            if mwst_code not in printed_mwst_codes:
                _mwst_satz = str(str(mwst_satz) + "%").ljust(13, " ")
                _mwst_total = str(frappe.utils.fmt_money(mwst_dict[mwst_satz]['total'])).ljust(10, " ")
                _mwst = str(frappe.utils.fmt_money(mwst_dict[mwst_satz]['mwst'])).ljust(4, " ")
                p.text("{mwst_code}{_mwst_satz}{_mwst_total}{_mwst}\n".format(mwst_code=mwst_code, _mwst_satz=_mwst_satz, _mwst_total=_mwst_total, _mwst=_mwst))
                printed_mwst_codes.append(mwst_code)
        
        p.text("\n\n")
        
        # MA Infos
        p.text("Es bediente Sie: {0}\n".format(frappe.db.get_value("User", sinv.owner, 'first_name')))
        p.text("Herzlichen Dank für Ihren Einkauf!\n\n")
        
        # RG Details
        p.text("Kunden-Nr.           {0}\n".format(sinv.customer))
        p.text("Rechnungs-Nr.        {0}\n".format(sinv.name))
        p.text("Datum / Uhrzeit:     {0}\n\n".format(sinv.creation.strftime("%d.%m.%Y / %H:%M")))
        p.set(align='center')
        p.qr("{0}".format(sinv.name), size=5)
        
        p.cut()
        return
    except Exception as err:
        frappe.log_error("{0}".format(err), "receipt_print() failed")
        return

@frappe.whitelist()
def quick_print(print_data=None):
    # connect printer
    enable_printouts = False if int(frappe.db.get_value("Worldline TIM", "Worldline TIM", 'printouts')) != 1 else True
    printer_ip = frappe.db.get_value("Worldline TIM", "Worldline TIM", 'printer_ip')
    if not printer_ip or not enable_printouts:
        return False
    try:
        p = connect_printer(printer_ip)
        p.charcode('USA')
        p.set(align='left')
        p.text("{0}\n".format(print_data))
        p.cut()
        return 1
    except Exception as err:
        frappe.log_error("{0}".format(err), "quick_print() failed")
        return False

def connect_printer(printer_ip):
    return printer.Network(printer_ip)

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

def _get_itemised_tax(doc):
    if not doc.taxes:
        return
    itemised_tax, itemised_taxable_amount = get_itemised_tax_breakup_data(doc)
    get_rounded_tax_amount(itemised_tax, doc.precision("tax_amount", "taxes"))
    return itemised_tax

def get_itemised_tax_breakup_data(doc):
    itemised_tax = get_itemised_tax(doc.taxes)

    itemised_taxable_amount = get_itemised_taxable_amount(doc.items)

    return itemised_tax, itemised_taxable_amount

def get_itemised_tax(taxes, with_tax_account=False):
    itemised_tax = {}
    for tax in taxes:
        if getattr(tax, "category", None) and tax.category=="Valuation":
            continue

        item_tax_map = json.loads(tax.item_wise_tax_detail) if tax.item_wise_tax_detail else {}
        if item_tax_map:
            for item_code, tax_data in item_tax_map.items():
                itemised_tax.setdefault(item_code, frappe._dict())

                tax_rate = 0.0
                tax_amount = 0.0

                if isinstance(tax_data, list):
                    tax_rate = flt(tax_data[0])
                    tax_amount = flt(tax_data[1])
                else:
                    tax_rate = flt(tax_data)

                itemised_tax[item_code][tax.description] = frappe._dict(dict(
                    tax_rate = tax_rate,
                    tax_amount = tax_amount
                ))

                if with_tax_account:
                    itemised_tax[item_code][tax.description].tax_account = tax.account_head

    return itemised_tax

def get_itemised_taxable_amount(items):
    itemised_taxable_amount = frappe._dict()
    for item in items:
        item_code = item.item_code or item.item_name
        itemised_taxable_amount.setdefault(item_code, 0)
        itemised_taxable_amount[item_code] += item.net_amount
    return itemised_taxable_amount

def get_rounded_tax_amount(itemised_tax, precision):
    # Rounding based on tax_amount precision
    for taxes in itemised_tax.values():
        for tax_account in taxes:
            taxes[tax_account]["tax_amount"] = flt(taxes[tax_account]["tax_amount"], precision)

@frappe.whitelist()
def create_sales_return_invoice(sinv_data):
    import json
    sinv = frappe.get_doc(json.loads(sinv_data))

    for sinv_item in sinv.items:
        sinv_item.qty = -1 * sinv_item.qty
        sinv_item.stock_qty = sinv_item.qty
        sinv_item.amount = sinv_item.qty * sinv_item.rate
    
    sinv.run_method("calculate_taxes_and_totals")

    for sinv_payments in sinv.payments:
        sinv_payments.amount = sinv.rounded_total
        sinv_payments.base_amount = sinv.rounded_total
    
    sinv.paid_amount = sinv.rounded_total
    sinv.base_paid_amount = sinv.rounded_total

    write_off_amount = False
    if flt(sinv.paid_amount) != flt(sinv.grand_total):
        if flt(sinv.paid_amount) > flt(sinv.grand_total):
            write_off_amount = flt(sinv.paid_amount) - flt(sinv.grand_total)
    
        if flt(sinv.grand_total) > flt(sinv.paid_amount):
            write_off_amount = flt(sinv.grand_total) - flt(sinv.paid_amount)
    
    if write_off_amount:
        sinv.write_off_amount = -1 * write_off_amount
        sinv.base_write_off_amount = -1 * write_off_amount
        sinv.write_off_outstanding_amount_automatically = 1
        sinv.run_method("calculate_taxes_and_totals")

    try:
        sinv.insert()
        sinv.submit()
    except:
        frappe.log_error(str(sinv.as_dict()), "Erstellung Gutschrift aus POS failed")
        frappe.throw("Die Gutschriften-Erstellung ist fehlgeschlagen.")
    
    return sinv

@frappe.whitelist()
def create_delivery_note(customer, items):
    import datetime
    import json
    items = json.loads(items)
    dn_items = []
    for item in items:
        dn_items.append({
            'item_code': item['item_code'],
            'qty': item['qty'],
            'rate': item['rate']
        })
    
    dn = frappe.get_doc({
        "doctype": "Delivery Note",
        "customer": customer,
        "items": dn_items,
        "delivery_date": datetime.datetime.now()
    })
    dn.insert()
    dn.submit()
    return dn.name

@frappe.whitelist()
def set_credit_details(eft_details, trans_seq, return_invoice):
    query = """
            UPDATE `tabSales Invoice`
            SET `eft_details` = '{eft_details}',
            `trans_seq` = '{trans_seq}'
            WHERE `name` = '{return_invoice}'
            """.format(eft_details=eft_details, \
                        trans_seq=trans_seq, \
                        return_invoice=return_invoice)
    update = frappe.db.sql(query, as_list=True)
    frappe.db.commit()
    return query
