frappe.ui.form.on('POS Profile', {
    test_print: function(frm) {
        frappe.call({
            method: "esag.esag.page.esagpos.esagpos.receipt_print",
            args: {
                test_print: cur_frm.doc.receipt_printer_ip
            },
            callback: function(r) {
                if (r.message == 1) {
                    frappe.msgprint("Der Testdruck war erfolgreich.");
                } else {
                    frappe.msgprint("Der Testdruck ist fehlgeschlagen");
                }
            }
        })
    }
});
