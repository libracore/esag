frappe.ui.form.on('Supplier', {
    before_save(frm) {
        if (!frm.doc.__islocal) {
            set_first_address(frm);
        }
    }
});

function set_first_address(frm) {
    frappe.call({
        'method': 'erpnextswiss.scripts.crm_tools.get_primary_supplier_address',
        'args': {
            'supplier': frm.doc.name
        },
        'async': false,
        'callback': function(response) {
            if (response.message) {
                var address = response.message;
                var adr_line = address.address_line1 + ", " + address.pincode + " " + address.city;
                cur_frm.set_value('hauptadresse', adr_line);
            }
        }
    });
}
