import frappe


def delivery_order_query(user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)

    if "DP Ops Manager" in roles:
        return "1=1"

    if "DP Rider" in roles:
        escaped_user = frappe.db.escape(user)

        return f"""
            `tabDelivery Order`.`assigned_rider` IN (
                SELECT `name`
                FROM `tabRider`
                WHERE `user` = {escaped_user}
            )
        """

    return "1=1"
