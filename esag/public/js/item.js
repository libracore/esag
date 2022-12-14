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
