frappe.ui.form.on('Purchase Order', {
    refresh(frm) {
        purify_purchase_taxes(frm);
        // attach_tax_observer();       // not working as expected
    },
    before_save(frm) {
        purify_purchase_taxes(frm);
    }
});

frappe.ui.form.on('Purchase Taxes and Charges', {
    /* tax_amount(frm, cdt, cdn) {          // does not trigger
        purify_purchase_taxes(frm);
    } */
});
