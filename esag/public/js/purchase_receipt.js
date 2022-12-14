frappe.ui.form.on('Purchase Receipt', {
    refresh(frm) {
        purify_purchase_taxes(frm);
    },
    before_save(frm) {
        purify_purchase_taxes(frm);
    }
});
