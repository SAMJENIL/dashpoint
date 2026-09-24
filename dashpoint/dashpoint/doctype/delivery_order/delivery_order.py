# Copyright (c) 2026, SAM JENIL and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class DeliveryOrder(Document):

    def validate(self):

        if not re.fullmatch(r"\d{10}", self.customer_phone or ""):
            frappe.throw(
                "Customer phone must contain exactly 10 digits."
            )

        statuses_requiring_rider = [
            "In Transit",
            "Delivery Failed",
            "Re-attempt Scheduled",
            "Delivered",
            "Escalated",
            "Cancelled",
        ]

        if (
            self.status in statuses_requiring_rider
            and not self.assigned_rider
        ):
            frappe.throw(
                f"Assigned Rider is required when status is '{self.status}'."
            )

        if self.status == "Delivery Failed" and not self.failure_reason:
            frappe.throw(
                "Failure Reason is required for a failed delivery."
            )

        self.packaging_total = 0

        for row in self.packaging_used:
            row.total_price = (
                (row.quantity or 0)
                * (row.unit_price or 0)
            )

            self.packaging_total += row.total_price

        if self.delivery_fee is None:
            self.delivery_fee = frappe.db.get_single_value(
                "Dispatch Settings",
                "default_delivery_fee"
            )

        self.final_amount = (
            (self.packaging_total or 0)
            + (self.delivery_fee or 0)
        )

    def before_submit(self):

        if self.status != "Delivered":
            frappe.throw(
                "Delivery Order can be submitted only when status is Delivered."
            )

        for row in self.packaging_used:

            stock_qty = frappe.db.get_value(
                "Packaging Material",
                row.material,
                "stock_qty"
            )

            if stock_qty < row.quantity:
                frappe.throw(
                    f"Insufficient stock for {row.material}. "
                    f"Available: {stock_qty}, Required: {row.quantity}"
                )

    def on_submit(self):

        for row in self.packaging_used:

            current_stock = frappe.db.get_value(
                "Packaging Material",
                row.material,
                "stock_qty"
            )

            frappe.db.set_value(
                "Packaging Material",
                row.material,
                "stock_qty",
                current_stock - row.quantity,
                update_modified=False,
            )

        receipt = frappe.get_doc({
            "doctype": "Delivery Receipt",
            "delivery_order": self.name,
            "delivery_fee": self.delivery_fee,
            "packaging_total": self.packaging_total,
            "total_amount": self.final_amount,
            "payment_status": (
                "Paid"
                if self.payment_status == "Paid"
                else "Unpaid"
            ),
        })

        receipt.insert(ignore_permissions=True)

        frappe.enqueue(
            "dashpoint.dashpoint.api.send_delivery_confirmation",
            delivery_order=self.name,
            queue="short",
        )

    @frappe.whitelist()
    def record_delivery_attempt(self, outcome, failure_reason=None):

        if outcome == "Failed":

            if not failure_reason:
                frappe.throw("Failure Reason is required.")

            self.failure_reason = failure_reason

            self.delivery_attempts_count = (
                self.delivery_attempts_count or 0
            ) + 1

            max_attempts = frappe.db.get_single_value(
                "Dispatch Settings",
                "max_delivery_attempts"
            )

            if self.delivery_attempts_count < max_attempts:
                self.status = "Re-attempt Scheduled"
            else:
                self.status = "Escalated"

        elif outcome == "Delivered":

            self.status = "Delivered"
            self.delivered_on = frappe.utils.now_datetime()

        else:
            frappe.throw(
                "Outcome must be either Failed or Delivered."
            )

        self.save()

        frappe.publish_realtime(
            "delivery_status_changed",
            {
                "delivery_order": self.name,
                "status": self.status
            },
            user=self.owner,
        )

    def on_cancel(self):

        self.status = "Cancelled"

        for row in self.packaging_used:

            current_stock = frappe.db.get_value(
                "Packaging Material",
                row.material,
                "stock_qty"
            )

            frappe.db.set_value(
                "Packaging Material",
                row.material,
                "stock_qty",
                current_stock + row.quantity,
                update_modified=False,
            )

        receipt_name = frappe.db.get_value(
            "Delivery Receipt",
            {"delivery_order": self.name},
            "name"
        )

        if receipt_name:

            receipt = frappe.get_doc(
                "Delivery Receipt",
                receipt_name
            )

            if receipt.docstatus == 1:
                receipt.cancel()

    def on_trash(self):

        if self.status not in ["Draft", "Cancelled"]:
            frappe.throw(
                "Delivery Order can only be deleted when status is Draft or Cancelled."
            )