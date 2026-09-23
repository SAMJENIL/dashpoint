import frappe


@frappe.whitelist()
def share_delivery_order(delivery_order_name, user_email):
    if not frappe.db.exists("Delivery Order", delivery_order_name):
        frappe.throw("Delivery Order does not exist")

    user = frappe.db.get_value("User", {"email": user_email}, "name")

    if not user:
        frappe.throw("User does not exist")

    frappe.share.add(
        "Delivery Order",
        delivery_order_name,
        user,
        read=1,
        write=0,
        share=0,
        everyone=0,
        notify=0,
    )

    return {
        "success": True,
        "message": f"Read access granted to {user_email}",
        "delivery_order": delivery_order_name,
    }


@frappe.whitelist()
def unsafe_delivery_order_data():
    return frappe.get_all("Delivery Order", fields="*")


@frappe.whitelist()
def safe_delivery_order_data():
    roles = frappe.get_roles(frappe.session.user)

    fields = [
        "name",
        "customer_name",
        "customer_phone",
        "customer_email",
        "delivery_zone",
        "assigned_rider",
        "status",
        "priority",
        "delivery_fee",
        "packaging_total",
        "final_amount",
        "payment_status",
    ]

    orders = frappe.get_list(
        "Delivery Order",
        fields=fields,
        order_by="modified desc",
    )

    if "DP Ops Manager" not in roles:
        for order in orders:
            order.pop("customer_phone", None)
            order.pop("customer_email", None)

    return orders


@frappe.whitelist()
def get_stuck_deliveries():
    from frappe.query_builder import DocType
    from frappe.utils import add_days, now_datetime

    DO = DocType("Delivery Order")

    cutoff = add_days(now_datetime(), -2)

    result = (
        frappe.qb.from_(DO)
        .select(
            DO.name,
            DO.customer_name,
            DO.assigned_rider,
            DO.creation,
        )
        .where(
            (DO.status.isin(["In Transit", "Re-attempt Scheduled"]))
            & (DO.creation < cutoff)
        )
        .orderby(DO.creation)
        .run(as_dict=True)
    )

    return result


@frappe.whitelist()
def reassign_zone(from_rider, to_rider):
    try:
        frappe.db.sql(
            """
            UPDATE `tabDelivery Order`
            SET assigned_rider = %s
            WHERE assigned_rider = %s
              AND status NOT IN ('Delivered', 'Cancelled')
            """,
            (to_rider, from_rider),
        )

        frappe.db.commit()

        return {
            "success": True,
            "message": (
                f"Open deliveries reassigned from "
                f"{from_rider} to {to_rider}"
            ),
        }

    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(),
            "Delivery Order Rider Reassignment Failed",
        )
        raise


def send_delivery_confirmation(delivery_order):
    frappe.logger().info(
        f"Delivery confirmation sent for {delivery_order}"
    )

def log_change(doc, method=None):
    if doc.doctype == "Audit Log":
        return

    frappe.get_doc({
        "doctype": "Audit Log",
        "doctype_name": doc.doctype,
        "document_name": doc.name,
        "action": method or "unknown",
        "user": frappe.session.user,
        "timestamp": frappe.utils.now_datetime(),
    }).insert(ignore_permissions=True)
