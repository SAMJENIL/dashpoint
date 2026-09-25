# Copyright (c) 2026, SAM JENIL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DeliveryReceipt(Document):
    def before_print(self, print_format=None):
        delivery_order = frappe.get_doc(
            "Delivery Order",
            self.delivery_order
        )

        self.delivery_zone = delivery_order.delivery_zone
        self.customer_phone = delivery_order.customer_phone
        self.customer_email = delivery_order.customer_email
        self.pickup_address = delivery_order.pickup_address
        self.packaging_used = delivery_order.packaging_used
        self.final_amount = delivery_order.final_amount

        self.payment_status = delivery_order.payment_status

        self.print_summary = (
            f"{self.customer_name} - {self.delivery_zone}"
        )