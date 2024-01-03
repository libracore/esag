# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, now, date_diff
from erpnext.stock.utils import add_additional_uom_columns
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition

from erpnext.stock.report.stock_ageing.stock_ageing import get_fifo_queue, get_average_age

from six import iteritems

def execute(filters=None):
    if not filters: filters = {}

    validate_filters(filters)

    from_date = filters.get('from_date')
    to_date = filters.get('to_date')

    include_uom = filters.get("include_uom")
    columns = get_columns(filters)
    items = get_items(filters)
    sle = get_stock_ledger_entries(filters, items)

    if filters.get('show_stock_ageing_data'):
        filters['show_warehouse_wise_stock'] = True
        item_wise_fifo_queue = get_fifo_queue(filters, sle)

    # if no stock ledger entry found return
    if not sle:
        return columns, []

    iwb_map = get_item_warehouse_map(filters, sle)
    item_map = get_item_details(items, sle, filters)
    item_reorder_detail_map = get_item_reorder_details(item_map.keys())

    data = []
    conversion_factors = {}
    for (company, item, warehouse) in sorted(iwb_map):
        if item_map.get(item):
            qty_dict = iwb_map[(company, item, warehouse)]
            item_reorder_level = 0
            item_reorder_qty = 0
            if item + warehouse in item_reorder_detail_map:
                item_reorder_level = item_reorder_detail_map[item + warehouse]["warehouse_reorder_level"]
                item_reorder_qty = item_reorder_detail_map[item + warehouse]["warehouse_reorder_qty"]
            # Add sales data to the existing stock ledger entries


            report_data = {
                'item_code': item,
                'warehouse': warehouse,
                'company': company,
                'reorder_level': item_reorder_qty,
                'reorder_qty': item_reorder_qty,
            }
            report_data.update(item_map[item])
            report_data.update(qty_dict)

            if include_uom:
                conversion_factors.setdefault(item, item_map[item].conversion_factor)

            if filters.get('show_stock_ageing_data'):
                fifo_queue = item_wise_fifo_queue[(item, warehouse)].get('fifo_queue')

                stock_ageing_data = {
                    'average_age': 0,
                    'earliest_age': 0,
                    'latest_age': 0
                }
                if fifo_queue:
                    fifo_queue = sorted(fifo_queue, key=lambda fifo_data: fifo_data[1])
                    stock_ageing_data['average_age'] = get_average_age(fifo_queue, to_date)
                    stock_ageing_data['earliest_age'] = date_diff(to_date, fifo_queue[0][1])
                    stock_ageing_data['latest_age'] = date_diff(to_date, fifo_queue[-1][1])

                report_data.update(stock_ageing_data)

            data.append(report_data)

    add_additional_uom_columns(columns, data, include_uom, conversion_factors)
    return columns, data

def get_columns(filters):
    """return columns"""

    columns = [
        {"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Item Name"), "fieldname": "item_name", "width": 150},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 100},
        {"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand", "width": 90},
        {"label": _("Description"), "fieldname": "description", "width": 140},
        {"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 100},
        {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Link", "options": "UOM", "width": 90},
        {"label": _("Balance Qty"), "fieldname": "bal_qty", "fieldtype": "Float", "width": 100, "convertible": "qty"},
        {"label": _("Balance Value"), "fieldname": "bal_val", "fieldtype": "Currency", "width": 100},
        {"label": _("Opening Qty"), "fieldname": "opening_qty", "fieldtype": "Float", "width": 100, "convertible": "qty"},
        {"label": _("Opening Value"), "fieldname": "opening_val", "fieldtype": "Float", "width": 110},
        {"label": _("In Qty"), "fieldname": "in_qty", "fieldtype": "Float", "width": 80, "convertible": "qty"},
        {"label": _("In Value"), "fieldname": "in_val", "fieldtype": "Float", "width": 80},
        {"label": _("Out Qty"), "fieldname": "out_qty", "fieldtype": "Float", "width": 80, "convertible": "qty"},
        {"label": _("Out Value"), "fieldname": "out_val", "fieldtype": "Float", "width": 80},
        {"label": _("Valuation Rate"), "fieldname": "val_rate", "fieldtype": "Currency", "width": 90, "convertible": "rate"},
        {"label": _("Reorder Level"), "fieldname": "reorder_level", "fieldtype": "Float", "width": 80, "convertible": "qty"},
        {"label": _("Reorder Qty"), "fieldname": "reorder_qty", "fieldtype": "Float", "width": 80, "convertible": "qty"},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 100},
        {"label": _("Sales Qty (Last 30 Days)"), "fieldname": "sales_qty_last_thirty_days", "fieldtype": "Float", "width": 120},
        {"label": _("Avg Consumption"), "fieldname": "avg_consumption_per_day", "fieldtype": "Float", "width": 100},
        {"label": _("Stock End Date"), "fieldname": "days_until_stock_ends", "fieldtype": "Data", "width": 100},
    ]

    if filters.get('show_stock_ageing_data'):
        columns += [{'label': _('Average Age'), 'fieldname': 'average_age', 'width': 100},
        {'label': _('Earliest Age'), 'fieldname': 'earliest_age', 'width': 100},
        {'label': _('Latest Age'), 'fieldname': 'latest_age', 'width': 100}]

    if filters.get('show_variant_attributes'):
        columns += [{'label': att_name, 'fieldname': att_name, 'width': 100} for att_name in get_variants_attributes()]

    return columns

def get_conditions(filters):
    conditions = ""
    if not filters.get("from_date"):
        frappe.throw(_("'From Date' is required"))

    if filters.get("to_date"):
        conditions += " and sle.posting_date <= %s" % frappe.db.escape(filters.get("to_date"))
    else:
        frappe.throw(_("'To Date' is required"))

    # ~ if filters.get("warehouse"):
        # ~ warehouse_details = frappe.db.get_value("Warehouse",
            # ~ filters.get("warehouse"), ["lft", "rgt"], as_dict=1)
        # ~ if warehouse_details:
            # ~ conditions += " and exists (select name from `tabWarehouse` wh \
                # ~ where wh.lft >= %s and wh.rgt <= %s and sle.warehouse = wh.name)"%(warehouse_details.lft,
                # ~ warehouse_details.rgt)

    if filters.get("warehouse_type") and not filters.get("warehouse"):
        conditions += " and exists (select name from `tabWarehouse` wh \
            where wh.warehouse_type = '%s' and sle.warehouse = wh.name)"%(filters.get("warehouse_type"))

    return conditions

def get_stock_ledger_entries(filters, items):
    item_conditions_sql = ''
    if items:
        item_conditions_sql = ' and sle.item_code in ({})'\
            .format(', '.join([frappe.db.escape(i, percent=False) for i in items]))

    conditions = get_conditions(filters)

    return frappe.db.sql("""
        select
            sle.item_code, warehouse, sle.posting_date, sle.actual_qty, sle.valuation_rate,
            sle.company, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference,
            sle.item_code as name, sle.voucher_no
        from
            `tabStock Ledger Entry` sle force index (posting_sort_index)
        where sle.docstatus < 2 %s %s
        order by sle.posting_date, sle.posting_time, sle.creation, sle.actual_qty""" % #nosec
        (item_conditions_sql, conditions), as_dict=1)

def get_sales_data():
    # Fetch sales data for the last 14 days
    sales_data = frappe.db.sql("""
        select
            sle.item_code,
            sle.warehouse,
            si.company,
            sum(sle.actual_qty) as sales_qty
        from
            `tabSales Invoice` si
            inner join `tabSales Invoice Item` sii on si.name = sii.parent
            inner join `tabStock Ledger Entry` sle on sii.item_code = sle.item_code
        where
            si.docstatus = 1
            and si.posting_date >= (CURDATE() -30)
            and si.posting_date <= %s
            and sle.voucher_type = 'Sales Invoice'
            and sle.actual_qty < 0
        group by
            sle.item_code, sle.warehouse
    """, (now()), as_dict=True)

    # Map sales data to the existing stock ledger entries
    sales_map = {(d.company, d.item_code, d.warehouse): d.sales_qty for d in sales_data}
    
    return sales_map

def get_item_warehouse_map(filters, sle):
    iwb_map = {}
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    sales_map = get_sales_data()

    for d in sle:
        key = (d.company, d.item_code, d.warehouse)
        if key not in iwb_map:
            iwb_map[key] = frappe._dict({
                "opening_qty": 0.0, "opening_val": 0.0,
                "in_qty": 0.0, "in_val": 0.0,
                "out_qty": 0.0, "out_val": 0.0,
                "bal_qty": 0.0, "bal_val": 0.0,
                "val_rate": 0.0, "sales_qty_last_thirty_days": 0.0
            })
        elif key in sales_map:
            iwb_map[key]['sales_qty_last_thirty_days'] = sales_map[key]

        qty_dict = iwb_map[(d.company, d.item_code, d.warehouse)]

        if d.voucher_type == "Stock Reconciliation":
            qty_diff = flt(d.qty_after_transaction) - qty_dict.bal_qty
        else:
            qty_diff = flt(d.actual_qty)

        value_diff = flt(d.stock_value_difference)

        if d.posting_date < from_date:
            qty_dict.opening_qty += qty_diff
            qty_dict.opening_val += value_diff

        elif d.posting_date >= from_date and d.posting_date <= to_date:
            if qty_diff > 0:
                qty_dict.in_qty += qty_diff
                qty_dict.in_val += value_diff
            else:
                qty_dict.out_qty += abs(qty_diff)
                qty_dict.out_val += abs(value_diff)

        qty_dict.val_rate = d.valuation_rate
        qty_dict.bal_qty += qty_diff
        qty_dict.bal_val += value_diff

    #iwb_map = filter_items_with_no_transactions(iwb_map)

    return iwb_map

def filter_items_with_no_transactions(iwb_map):
    for (company, item, warehouse) in sorted(iwb_map):
        qty_dict = iwb_map[(company, item, warehouse)]

        no_transactions = True
        float_precision = cint(frappe.db.get_default("float_precision")) or 3
        for key, val in iteritems(qty_dict):
            val = flt(val, float_precision)
            qty_dict[key] = val
            if key != "val_rate" and val:
                no_transactions = False

        if no_transactions:
            iwb_map.pop((company, item, warehouse))

    return iwb_map

def get_items(filters):
    conditions = []
    if filters.get("item_code"):
        conditions.append("item.name=%(item_code)s")
    else:
        if filters.get("brand"):
            conditions.append("item.brand=%(brand)s")
        if filters.get("item_group"):
            conditions.append(get_item_group_condition(filters.get("item_group")))

    items = []
    if conditions:
        items = frappe.db.sql_list("""select name from `tabItem` item where {}"""
            .format(" and ".join(conditions)), filters)
    return items

def get_item_details(items, sle, filters):
    item_details = {}
    if not items:
        items = list(set([d.item_code for d in sle]))

    if not items:
        return item_details

    cf_field = cf_join = ""
    if filters.get("include_uom"):
        cf_field = ", ucd.conversion_factor"
        cf_join = "left join `tabUOM Conversion Detail` ucd on ucd.parent=item.name and ucd.uom=%s" \
            % frappe.db.escape(filters.get("include_uom"))

    res = frappe.db.sql("""
        select
            item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom %s, bin.actual_qty as stock_in_sku, bin.ordered_qty as ordered_qty,
            (select sum(dni.qty) / 180
             from `tabDelivery Note Item` as dni
             left join `tabDelivery Note` as dn on dn.name = dni.parent
             WHERE  dni.item_code = item.item_code
                   AND dni.docstatus = 1
                   AND dn.posting_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 180 DAY) AND CURDATE()
            ) as avg_consumption_per_day,
            0 as days_until_stock_ends
        from
            `tabItem` item
        left join `tabBin` as bin on bin.item_code = item.item_code
            %s
        where
            item.name in (%s) and ifnull(item.disabled, 0) = 0
    """ % (cf_field, cf_join, ','.join(['%s'] *len(items))), items, as_dict=1)

    for item in res:
        item_details.setdefault(item.name, item)
        if item.avg_consumption_per_day:
            frappe.msgprint("{0}".format(item.avg_consumption_per_day))
            days_until_stock_ends = round((item['stock_in_sku'] + item['ordered_qty']) / item['avg_consumption_per_day'], 2)
            item['days_until_stock_ends'] = frappe.utils.data.add_to_date(date=frappe.utils.data.today(), days=days_until_stock_ends, as_string=True)
        else:
            item['days_until_stock_ends'] = ""

    if filters.get('show_variant_attributes', 0) == 1:
        variant_values = get_variant_values_for(list(item_details))
        item_details = {k: v.update(variant_values.get(k, {})) for k, v in iteritems(item_details)}

    return item_details

def get_item_reorder_details(items):
    item_reorder_details = frappe._dict()

    if items:
        item_reorder_details = frappe.db.sql("""
            select parent, warehouse, warehouse_reorder_qty, warehouse_reorder_level
            from `tabItem Reorder`
            where parent in ({0})
        """.format(', '.join([frappe.db.escape(i, percent=False) for i in items])), as_dict=1)

    return dict((d.parent + d.warehouse, d) for d in item_reorder_details)

def validate_filters(filters):
    if not (filters.get("item_code") or filters.get("warehouse")):
        sle_count = flt(frappe.db.sql("""select count(name) from `tabStock Ledger Entry`""")[0][0])
        if sle_count > 500000:
            frappe.throw(_("Please set filter based on Item or Warehouse"))

def get_variants_attributes():
    '''Return all item variant attributes.'''
    return [i.name for i in frappe.get_all('Item Attribute')]

def get_variant_values_for(items):
    '''Returns variant values for items.'''
    attribute_map = {}
    for attr in frappe.db.sql('''select parent, attribute, attribute_value
        from `tabItem Variant Attribute` where parent in (%s)
        ''' % ", ".join(["%s"] * len(items)), tuple(items), as_dict=1):
            attribute_map.setdefault(attr['parent'], {})
            attribute_map[attr['parent']].update({attr['attribute']: attr['attribute_value']})

    return attribute_map
