// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('User', {
    refresh: function(frm) {
        frm.add_custom_button(__("POS QR Generation"), function() {
                frappe.prompt([
                    {'fieldname': 'pwd', 'fieldtype': 'Password', 'label': __('Please Enter Your Password to Continue'), 'reqd': 1}  
                ],
                function(values){
                    frappe.call({
                        method: "esag.esag.page.esagpos.esagpos.get_esag_pos_qr",
                        args:{
                            'user': cur_frm.doc.name,
                            'pwd': values.pwd
                        },
                        async: false,
                        callback: function(r) {
                            const hash = r.message;
                            const template = `
                                <div>
                                    <p><b>Raw</b></p>
                                    <p>${hash}</p>
                                </div>
                                <div>
                                    <p><b>QR</b></p>
                                    <img src="https://data.libracore.ch/phpqrcode/api/qrcode.php?content=${hash}&ecc=H&size=6&frame=2"/>
                                </div>
                            `;
                            frappe.msgprint(template, "POS QR");
                        }
                    });
                },
                __('POS QR Generation'),
                __('Generate')
                )
            }).addClass("btn-warning")
    }
});
