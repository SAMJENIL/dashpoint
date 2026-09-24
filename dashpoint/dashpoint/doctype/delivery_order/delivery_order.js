// Copyright (c) 2026, SAM JENIL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Delivery Order", {
    setup(frm) {
        frm.set_query("assigned_rider", function () {
            return {
                filters: {
                    status: "Active",
                    assigned_zone: frm.doc.delivery_zone
                }
            };
        });
    },

    refresh(frm) {
        const status_colors = {
            "Draft": "gray",
            "In Transit": "blue",
            "Delivery Failed": "red",
            "Re-attempt Scheduled": "orange",
            "Delivered": "green",
            "Escalated": "red",
            "Cancelled": "gray"
        };

        if (frm.doc.status) {
            frm.dashboard.add_indicator(frm.doc.status,
                status_colors[frm.doc.status] || "gray");
        }


        if (
            ["In Transit", "Re-attempt Scheduled"].includes(
                frm.doc.status
            )
        ) {
            frm.add_custom_button("Log Delivery Attempt", function () {
                frm.trigger("log_delivery_attempt");
            });
        }


        frm.add_custom_button("Reassign Rider", function () {
            if (!frm.doc.assigned_rider) {
                frappe.msgprint("No rider is currently assigned.");
                return;
            }

            frappe.prompt(
                [
                    {
                        label: "New Rider",
                        fieldname: "new_rider",
                        fieldtype: "Link",
                        options: "Rider",
                        reqd: 1
                    }
                ],
                function (values) {
                    if (values.new_rider === frm.doc.assigned_rider) {
                        frappe.msgprint(
                            "Please select a different rider."
                        );
                        return;
                    }

                    frappe.confirm(
                        `Are you sure you want to reassign this delivery from ${frm.doc.assigned_rider} to ${values.new_rider}?`,
                        function () {
                            frappe.call({
                                method: "dashpoint.dashpoint.api.reassign_zone",
                                args: {
                                    from_rider: frm.doc.assigned_rider,
                                    to_rider: values.new_rider
                                },
                                callback: function (r) {
                                    if (
                                        r.message &&
                                        r.message.success
                                    ) {
                                        frappe.msgprint(
                                            r.message.message
                                        );

                                        frm.trigger("assigned_rider");
                                        frm.reload_doc();
                                    }
                                }
                            });
                        }
                    );
                },
                "Reassign Rider",
                "Reassign"
            );
        });
    },

    assigned_rider(frm) {
        if (
            !frm.doc.assigned_rider ||
            !frm.doc.delivery_zone
        ) {
            return;
        }

        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Rider",
                filters: {
                    name: frm.doc.assigned_rider
                },
                fieldname: "assigned_zone"
            },
            callback: function (r) {
                if (
                    r.message &&
                    r.message.assigned_zone !== frm.doc.delivery_zone) {
                    frappe.msgprint({
                        title: "Zone Mismatch",
                        message:
                            "The assigned rider belongs to " +
                            r.message.assigned_zone +
                            ", but this Delivery Order is for " +
                            frm.doc.delivery_zone + ".",
                        indicator: "orange"
                    });
                }
            }
        });
    },

    log_delivery_attempt(frm) {
        const dialog = new frappe.ui.Dialog({
            title: "Log Delivery Attempt",

            fields: [
                {
                    label: "Outcome",
                    fieldname: "outcome",
                    fieldtype: "Select",
                    options: "Delivered\nFailed",
                    reqd: 1
                },
                {
                    label: "Failure Reason",
                    fieldname: "failure_reason",
                    fieldtype: "Select",
                    options:
                        "Customer Unavailable\nWrong Address\nRefused\nOther",
                    reqd: 1
                }
            ],

            primary_action_label: "Submit",

            primary_action(values) {
                if (
                    values.outcome === "Failed" &&
                    !values.failure_reason
                ) {
                    frappe.msgprint(
                        "Failure Reason is required."
                    );
                    return;
                }

                frm.call(
                    "record_delivery_attempt",
                    {
                        outcome: values.outcome,
                        failure_reason: values.failure_reason
                    }
                ).then(() => {
                    dialog.hide();
                    frm.reload_doc();
                });
            }
        });

        dialog.show();
    }
});

frappe.ui.form.on("Packaging Usage Entry", {
    quantity(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        const total =
            (row.quantity || 0) *
            (row.unit_price || 0);

        frappe.model.set_value(
            cdt,
            cdn,
            "total_price",
            total
        );
    }
});