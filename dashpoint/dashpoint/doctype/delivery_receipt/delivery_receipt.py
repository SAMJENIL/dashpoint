# Copyright (c) 2026, SAM JENIL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DeliveryReceipt(Document):
    def before_print(self, print_format=None):
        delivery_zone = frappe.db.get_value(
            "Delivery Order",
            self.delivery_order,
            "delivery_zone"
        )

        self.print_summary = f"{self.customer_name} - {delivery_zone}"