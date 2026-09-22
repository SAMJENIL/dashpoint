# Copyright (c) 2026, SAM JENIL and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class PackagingMaterial(Document):
	def autoname(self):
		self.material_code = self.material_code.upper()
		self.name = frappe.model.naming.make_autoname("PKG-.YYYY.-.####")

	def validate(self):
		if self.charge_to_customer < self.unit_cost:
			frappe.throw("Charge to Customer cannot be less than Unit Cost")

