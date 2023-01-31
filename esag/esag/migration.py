# Copyright (c) 2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from erpnextswiss.scripts.crm_tools import get_primary_supplier_address, get_primary_customer_address

def set_supplier_first_address():
    suppliers = frappe.get_all("Supplier", filters={'disabled': 0}, fields=['name'])
    for supplier in suppliers:
        s = frappe.get_doc("Supplier", supplier['name'])
        address = get_primary_supplier_address(s.name)
        if address:
            s.hauptadresse = "{0}, {1}, {2} {3}".format(address.address_line1 or "", address.address_line2 or "", address.pincode or "", address.city or "")
            s.save()
            print("Updated {0}".format(s.name))
    return
    
def set_customer_first_address():
    customers = frappe.get_all("Customer", filters={'disabled': 0}, fields=['name'])
    for customer in customers:
        c = frappe.get_doc("Customer", customer['name'])
        address = get_primary_customer_address(c.name)
        if address:
            c.hauptadresse = "{0}, {1}, {2} {3}".format(address.address_line1 or "", address.address_line2 or "", address.pincode or "", address.city or "")
            c.save()
            print("Updated {0}".format(c.name))
    return
