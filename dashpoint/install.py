import frappe


def after_install():
    default_zones = [
        {
            "zone_name": "North Zone",
            "description": "Delivery in north zone area",
            "avg_delivery_hours": 2,
        },
        {
            "zone_name": "Central Zone",
            "description": "Delivery in central zone area",
            "avg_delivery_hours": 1,
        },
        {
            "zone_name": "South Zone",
            "description": "Delivery in south zone area",
            "avg_delivery_hours": 2,
        },
    ]

    for zone in default_zones:
        if not frappe.db.exists("Delivery Zone", zone["zone_name"]):
            frappe.get_doc({
                "doctype": "Delivery Zone",
                **zone,
            }).insert(ignore_permissions=True)

    if not frappe.db.exists("Dispatch Settings"):
        frappe.get_doc({
            "doctype": "Dispatch Settings",
            "dispatch_center_name": "Default Dispatch Center",
            "ops_manager_email": "ops@dashpoint.local",
            "max_delivery_attempts": 3,
            "default_delivery_fee": 60,
            "low_stock_alert_enabled": 1,
        }).insert(ignore_permissions=True)

    frappe.db.commit()
    frappe.msgprint("DashPoint default data seeded successfully.")
