frappe.query_reports["Active Deliveries"] = {
    filters: [
        {
            fieldname: "delivery_zone",
            label: __("Delivery Zone"),
            fieldtype: "Link",
            options: "Delivery Zone",
            default: "%"
        }
    ]
};
