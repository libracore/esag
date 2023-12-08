frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        if (cur_frm.doc.docstatus == 1) {
            if (cur_frm.doc.is_pos == 1) {
                if (cur_frm.doc.is_return == 1) {
                    frm.add_custom_button(__("Gutschrift Ausbezahlen"), function() {
                        alert("Hello World!");
                    });
                    frm.add_custom_button(__("Gutschrift ins POS übertragen"), function() {
                        localStorage.setItem('POSGutschrift', cur_frm.doc.name);
                        localStorage.setItem('POSGutschriftBetrag', cur_frm.doc.paid_amount);
                        frappe.set_route("esagpos");
                    });
                }
            }
        }
    }
});
