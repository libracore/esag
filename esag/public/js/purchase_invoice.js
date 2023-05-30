frappe.ui.form.on('Purchase Invoice', {
    refresh(frm) {
        purify_purchase_taxes(frm);
    },
    before_save(frm) {
        purify_purchase_taxes(frm);
        
        // check attachments
        if (!frm.doc.__islocal) {
            if (cur_frm.attachments.get_attachments().length === 0) {
                frappe.throw( "Bitte ein Original beifügen" );
            } 
        }
    }
});
