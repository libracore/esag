/* common functions for ESAG */

// this function removes VAT entries from purchase documents
function purify_purchase_taxes(frm) {
    if (frm.doc.taxes) {
        for (var i = frm.doc.taxes.length; i > 0; i--) {
            if (frm.doc.taxes[i - 1].account_head.startsWith("22")) {
                cur_frm.get_field("taxes").grid.grid_rows[i - 1].remove();
            }
        }
        cur_frm.refresh_fields('taxes');
    }
}

// mutation observer for tax changes
var tax_observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        purify_purchase_taxes(cur_frm);
    });
});

function attach_tax_observer() {
    var target = document.querySelector('div[data-fieldname="total_taxes_and_charges"] .control-input-wrapper .control-value');
    var options = {
        attributes: true,
        characterData: true
    };
    tax_observer.observe(target, options);
}
