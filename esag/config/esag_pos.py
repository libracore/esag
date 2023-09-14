from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
        {
            "label": _("Selling"),
            "icon": "fa fa-users",
            "items": [
                    {
                       "type": "page",
                       "name": "esagpos",
                       "label": _("POS"),
                       "description": _("ESAG POS")
                    }
            ]
        }
    ]
