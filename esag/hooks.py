# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "esag"
app_title = "ESAG"
app_publisher = "libracore"
app_description = "ETH Store AG ERP applications"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@libracore.com"
app_license = "AGPL"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/esag/css/esag.css"
app_include_js = [
    "/assets/esag/js/esag_common.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/esag/css/esag.css"
# web_include_js = "/assets/esag/js/esag.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Purchase Order" : "public/js/purchase_order.js",
    "Purchase Receipt" : "public/js/purchase_receipt.js",
    "Purchase Invoice" : "public/js/purchase_invoice.js",
    "Sales Invoice" : "public/js/sales_invoice.js",
    "Customer" : "public/js/customer.js",
    "Supplier" : "public/js/supplier.js",
    "Item" : "public/js/item.js",
    "User" : "public/js/user.js",
    "POS Profile" : "public/js/pos_profile.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "esag.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "esag.install.before_install"
# after_install = "esag.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "esag.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Sales Invoice": {
        "on_submit": "esag.esag.sales_invoice.sales_invoice.check_gutschein"
    }
}

# Scheduled Tasks
# ---------------
scheduler_events = {
    "daily": [
        "esag.esag.utils.clearing_rounding_differences"
    ]
}
# scheduler_events = {
# 	"all": [
# 		"esag.tasks.all"
# 	],
# 	"daily": [
# 		"esag.tasks.daily"
# 	],
# 	"hourly": [
# 		"esag.tasks.hourly"
# 	],
# 	"weekly": [
# 		"esag.tasks.weekly"
# 	]
# 	"monthly": [
# 		"esag.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "esag.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "esag.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "esag.task.get_dashboard_data"
# }

