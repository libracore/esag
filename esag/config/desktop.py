# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
    return [
        {
            "module_name": "ESAG",
            "color": "grey",
            "icon": "octicon octicon-file-directory",
            "type": "module",
            "label": _("ESAG")
        },
        {
            "module_name": "ESAG POS",
            "color": "grey",
            "icon": "icon retail-blue",
            "type": "module",
            "label": _("ESAG POS")
        }
    ]
