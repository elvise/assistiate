# -*- coding: utf-8 -*-
# Copyright (c) 2017, Syed Abdul Qadeer and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
import frappe.utils
from frappe import _

def validate(self, method):
    for d in self.get('purposes'):
        if d.serial_no and not frappe.db.exists({
            "doctype": "Serial No",
            "warehouse": d.warehouse,
            "item_code": d.item_code
        }, d.serial_no):
            frappe.throw(_("Serial No {0} does not exist").format(d.serial_no))

def on_submit(self, method):
	for item in self.get("purposes"):
		if not (item.prevdoc_doctype and item.prevdoc_doctype == "Sales Order" and
				item.prevdoc_docname and item.serial_no):
			return

		if not frappe.db.sql("""select name from `tabSales Order` where name=%s""", item.prevdoc_docname):
			return

		serial_no_data = frappe.db.get_value("Sales Order Item", {
			"parent": item.prevdoc_docname,
			"parenttype": item.prevdoc_doctype,
			"item_code": item.item_code,
            "name": item.prevdoc_detail_docname
		}, ["serial_no", "name"])

		if serial_no_data:
			splitted = []
			if serial_no_data[0]:
				splitted = serial_no_data[0].split("\n")
			if item.serial_no not in splitted:
				splitted.append(item.serial_no)

			joined = "\n".join(splitted)

			frappe.db.set_value("Sales Order Item", serial_no_data[1], "serial_no", joined,
								update_modified=False)

	update_sales_order_items(self)

def update_sales_order_items(self):
	from erpnext.stock.get_item_details import get_item_details
	from frappe.model.meta import default_fields

	sales_order_exists = (len(self.get("purposes", {"prevdoc_doctype" : "Sales Order"})) > 0)

	if not sales_order_exists:
		return

	sales_order = None

	for item in self.get("purposes", {"prevdoc_doctype" : "Sales Order"}):
		if item.prevdoc_docname or not (item.prevdoc_doctype and
												item.prevdoc_doctype=="Sales Order"):
			return

		if not sales_order:
			sales_order = frappe.get_doc("Sales Order", item.prevdoc_docname)

		elif not sales_order.name == item.prevdoc_docname:
				frappe.throw(_("You cannot have multiple Sales Order in the Assistance"))

		if not sales_order.docstatus == 0:
			continue

		out = get_item_details({
					"item_code": item.item_code,
					"serial_no": item.serial_no,
					"warehouse": item.warehouse,
					"customer": sales_order.customer,
					"currency": sales_order.currency,
					"conversion_rate": sales_order.conversion_rate,
					"price_list": sales_order.selling_price_list,
					"price_list_currency": sales_order.price_list_currency,
					"plc_conversion_rate": sales_order.plc_conversion_rate,
					"company": sales_order.company,
					"order_type": sales_order.order_type,
					"transaction_date": sales_order.transaction_date,
					"ignore_pricing_rule": sales_order.ignore_pricing_rule,
					"doctype": sales_order.doctype,
					"name": sales_order.name,
					"project": sales_order.project,
					"qty": item.qty or 1,
					"stock_qty": None,
					"conversion_factor": None,
					"is_pos": 0,
					"update_stock": 0
			})

		del out["doctype"]
		del out["name"]

		child_item = sales_order.append({})

		for key, value in out.items():
			if hasattr(child_item, key):
				child_item.set(key, value, as_value=True);

		sales_order.save()

	pass

def on_cancel(self, method):
	pass
