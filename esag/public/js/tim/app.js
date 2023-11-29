// Create namespace for our example ecr
simpleEcr = {};

// Extend the DefaultTerminalListener
class timapiListener extends timapi.DefaultTerminalListener {

    // Called if the state of the terminal changed. Retrieve the state using terminal.getTerminalState().
    terminalStatusChanged(terminal) {
        super.terminalStatusChanged(terminal);
        let terminalStatus = terminal.getTerminalStatus();
        console.log("Terminal Status: " + terminalStatus);
        updateDisplayContent(terminalStatus);
    }

    // Called by all of the other request specific methods unless they are implemented differently
    requestCompleted(event, data){
        super.requestCompleted(event, data);
        console.log("Request of type "+ event.requestType + " completed...");
        if(event.exception !== undefined) {
            console.log("Exception:" + event.exception);
        }
        if(data !== undefined) {
            console.log("Request data:" + data);
        }
    }

    // Called if a request started with {@link timapi.Terminal#connectAsync connectAsync} finished.
    connectCompleted(event){
        super.connectCompleted(event);
        console.log(event);
    }

    // Called if a request started with {@link timapi.Terminal#transactionAsync transactionAsync} finished.
    transactionCompleted(event, data){
        super.transactionCompleted(event, data);

        // Get transaction information to extract transaction reference numbers.
        // These can be used in a following transaction e.g. in case of reversal.
        if (data != undefined && data.transactionInformation != undefined) {
            switch (data.transactionType) {
                case timapi.constants.TransactionType.purchase:
                    if (event.exception === undefined) {
                        if (data.printData.receipts) {
                            if (data.printData.receipts.length > 1) {
                                cur_dialog.set_df_property('six_status', 'options', '<div width="20" height="20" style="background-color: green;"><center>Zahlungsprozess abgeschlossen</center></div>');
                                cur_frm.set_value("eft_details", data.printData.receipts[data.printData.receipts.length - 1].value);
                                cur_frm.set_value("trans_seq", data.transactionInformation.transSeq);
                                cur_dialog.set_df_property('ecr_cancel', 'hidden', 1);
                                console.log("--------------------------------------------------------------------------------------");
                                console.log("[libracore] Verkauf abgeschlossen");
                                console.log("[libracore]\n" + data.printData.receipts[data.printData.receipts.length - 1].value);
                                console.log("--------------------------------------------------------------------------------------");
                            }
                        }
                    } else {
                        var error_message = event.exception.errorMessage;
                        cur_dialog.set_df_property('six_status', 'options', '<div width="20" height="20" style="background-color: red;"><center>' + error_message + '</center></div>');
                        cur_dialog.set_df_property('ecr_cancel', 'hidden', 1);
                    }
                    break;
                case timapi.constants.TransactionType.credit:
                    if (event.exception === undefined) {
                        if (data.printData.receipts) {
                            if (data.printData.receipts.length > 1) {
                                console.log("--------------------------------------------------------------------------------------");
                                console.log("[libracore] Gutschrift abgeschlossen");
                                console.log("[libracore]\n" + data.printData.receipts[data.printData.receipts.length - 1].value);
                                console.log("--------------------------------------------------------------------------------------");
                                frappe.call({
                                    method: "esag.esag.page.esagpos.esagpos.quick_print",
                                    args: {
                                        print_data: data.printData.receipts[data.printData.receipts.length - 1].value
                                    }
                                });
                            }
                        }
                    } else {
                        var error_message = event.exception.errorMessage;
                        frappe.throw(error_message);
                    }
                    break;
                case timapi.constants.TransactionType.reversal:
                    if (event.exception === undefined) {
                        if (data.printData.receipts) {
                            if (data.printData.receipts.length > 1) {
                                console.log("--------------------------------------------------------------------------------------");
                                console.log("[libracore] Rückabwicklung abgeschlossen");
                                console.log("[libracore]\n" + data.printData.receipts[data.printData.receipts.length - 1].value);
                                console.log("--------------------------------------------------------------------------------------");
                                frappe.call({
                                    method: "esag.esag.page.esagpos.esagpos.quick_print",
                                    args: {
                                        print_data: data.printData.receipts[data.printData.receipts.length - 1].value
                                    }
                                });
                            }
                        }
                    } else {
                        var error_message = event.exception.errorMessage;
                        frappe.throw(error_message);
                    }
                    break;
                default:
                    console.log("--------------------------------------------------------------------------------------");
                    console.log("[libracore] Transaktion wird nicht getrackt (keine von Verkauf, Gutschrift, Rückabwicklung)");
                    console.log("--------------------------------------------------------------------------------------");
                    break;
            }
        } else {
            if (event.exception) {
                var error_message = event.exception.errorMessage;
                cur_dialog.set_df_property('six_status', 'options', '<div width="20" height="20" style="background-color: red;"><center>' + error_message + '</center></div>');
                cur_dialog.set_df_property('ecr_cancel', 'hidden', 1);
            }
        }
    }
    
    // print method for shift activations
    activateCompleted(event, data){
        super.activateCompleted(event, data);
        if (data.printData.receipts) {
            if (data.printData.receipts.length > 0) {
                frappe.call({
                    method: "esag.esag.page.esagpos.esagpos.quick_print",
                    args: {
                        print_data: data.printData.receipts[0].value
                    }
                });
            }
        }
                console.log("habe gemacht activateCompleted");
    }
    
    // print method for daily-closings
    balanceCompleted(event, data){
        super.balanceCompleted(event, data);
        if (data.printData.receipts) {
            if (data.printData.receipts.length > 0) {
                frappe.call({
                    method: "esag.esag.page.esagpos.esagpos.quick_print",
                    args: {
                        print_data: data.printData.receipts[0].value
                    }
                });
            }
        }
    }
}

// Initalizes the tim api
function initTimApi() {	
    // Create settings with IP-address and port of terminal to connect to
    let settings = new timapi.TerminalSettings();
    
    frappe.db.get_doc("Worldline TIM", "Worldline TIM").then(function(details){
        // IP-address and port of terminal to connect to
        settings.connectionIPString = details.connectionipstring;
        settings.connectionIPPort = details.connectionipport;

        // The integrator id to identify the integrator
        settings.integratorId = details.integratorid;

        // Deactivate fetch brands and auto commit
        settings.fetchBrands = false;
        settings.autoCommit = parseInt(details.autocommit) == 1 ? true:false;

        // Create terminal
        simpleEcr.terminal = new timapi.Terminal(settings);

        // Add user data
        var pos_id = details.pos_id ? details.pos_id:'ECR-Default';
        simpleEcr.terminal.setPosId(pos_id);
        simpleEcr.terminal.setUserId(1);

        // Add customized listener
        simpleEcr.terminal.addListener(new timapiListener());
    });
}

// Update ui with terminal status data
function updateDisplayContent(terminalStatus) {
    if (terminalStatus !== undefined) {
        var text = '';
        if (terminalStatus.displayContent.length > 0) {
            text = terminalStatus.displayContent[0];
        }
        $('.display-line1').each(function(){
            $(this).text(text);
            if (text == '') {
                $(this).append('&nbsp;');
            }
        });

        text = '';
        if (terminalStatus.displayContent.length > 1) {
            text = terminalStatus.displayContent[1];
        }
        $('.display-line2').each(function(){
            $(this).text(text);
            if (text == '') {
                $(this).append('&nbsp;');
            }
        });
    }
}

// init tim api after loading this script
initTimApi();
