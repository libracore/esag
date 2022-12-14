frappe.ui.form.on('Purchase Invoice', {
    refresh(frm) {
        purify_purchase_taxes(frm);
    },
    before_save(frm) {
        purify_purchase_taxes(frm);
    }
});
