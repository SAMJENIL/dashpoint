import frappe


def check_stuck_reattempts():
    
    today = frappe.utils.today()

    last_run = frappe.db.get_value(
        "Audit Log",
        {
            "action": "stuck_reattempt_check",
            "creation": [">=", f"{today} 00:00:00"],
        },
        "name",
    )

    if last_run:
        return

    cutoff = frappe.utils.add_to_date(
        frappe.utils.now_datetime(),
        hours=-24,
    )

    stuck_orders = frappe.get_list(
        "Delivery Order",
        filters={
            "status": "Re-attempt Scheduled",
            "modified": ["<", cutoff],
        },
        fields=["name", "assigned_rider", "modified"],
    )

    ops_manager_email = frappe.db.get_single_value(
        "Dispatch Settings",
        "ops_manager_email",
    )

    for order in stuck_orders:
        frappe.get_doc({
            "doctype": "Audit Log",
            "doctype_name": "Delivery Order",
            "document_name": order.name,
            "action": "stuck_reattempt",
            "user": frappe.session.user,
            "timestamp": frappe.utils.now_datetime(),
        }).insert(ignore_permissions=True)

    if stuck_orders and ops_manager_email:
        order_names = ", ".join(
            order.name for order in stuck_orders
        )

        frappe.sendmail(
            recipients=[ops_manager_email],
            subject="DashPoint: Stuck Re-attempt Deliveries",
            message=(
                "The following Delivery Orders have been in "
                f"Re-attempt Scheduled status for more than 24 hours: "
                f"{order_names}"
            ),
        )
        
    frappe.get_doc({
        "doctype": "Audit Log",
        "doctype_name": "Delivery Order",
        "document_name": "SCHEDULED_JOB",
        "action": "stuck_reattempt_check",
        "user": frappe.session.user,
        "timestamp": frappe.utils.now_datetime(),
    }).insert(ignore_permissions=True)

    frappe.db.commit()