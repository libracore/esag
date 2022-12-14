frappe.ui.form.on('Item', {
    refresh(frm) {
        if (frm.doc.__islocal) {
            frm.add_custom_button("Merchandise", function() {
                get_item_code(0);
            }, __("Artikelcode") );
            frm.add_custom_button("Kundenartikel", function() {
                get_item_code(1);
            }, __("Artikelcode") );
        }
        
        frm.add_custom_button("Barcode erzeugen", function() {
            get_barcode();
        }, __("Artikelcode") );
    }
});

function get_item_code(customer_order) {
    frappe.call({
        'method': 'esag.esag.utils.get_next_item_code',
        'args': {
            'customer_order': customer_order
        },
        'callback': function(response) {
            if (response.message) {
                cur_frm.set_value('item_code', response.message);
            }
        }
    });
}

function get_barcode() {
    frappe.call({
        'method': 'esag.esag.utils.get_next_barcode',
        'callback': function(response) {
            if (response.message) {
                if ((cur_frm.doc.barcodes) && (cur_frm.doc.barcodes.length > 0)) {
                    frappe.model.set_value(cur_frm.doc.barcodes[0].doctype, cur_frm.doc.barcodes[0].name, 'barcode', response.message);
                } else {
                    var child = cur_frm.add_child('barcodes');
                    frappe.model.set_value(child.doctype, child.name, 'barcode', response.message);
                }
                cur_frm.refresh_fields('barcode');
            }
        }
    });
}
