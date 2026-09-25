# DashPoint

## B2c — Dangerous Document Lifecycle Bugs

### Bug 1

Calling self.save() inside validate() is wrong because validate() already runs during save. It can call itself again and again, causing a recursion error.

#### Corrected Code

```python
def validate(self):
    self.packaging_total = sum(
        r.total_price for r in self.packaging_used
    ) 

### Bug 2

Changing stock inside validate() is wrong because validate() can run multiple times before submission. This can cause the stock to be deducted multiple times. Stock should be updated only during submission.

#### Corrected Code

def on_submit(self):
    material = frappe.get_doc(
        "Packaging Material",
        self.packaging_used[0].material
    )

    material.stock_qty -= self.packaging_used[0].quantity
    material.save() 

####b2d

If two people edit the same Delivery Order, the first person who saves it makes the latest changes. When the second person tries to save their old version, Frappe detects the change and shows an error instead of overwriting the first person's work. 


## C3 

I renamed RDR-0002 to RDR-0003 using frappe.rename_doc() with merge=False. The linked Delivery Order automatically updated its assigned_rider to RDR-0003. frappe updates the link fields when the document is renamed.  

##E1 

self.save() inside on_update() is dangerous because saving the document calls on_update() again. This creates a loop where on_update() keeps calling itself, which can cause a recursion error.


###E2 

merge=True combines the old document into an existing document with the new name. This can cause the old record's data to be merged or lost, so it should only be used when we intentionally want to combine two records.

###E3 

I will use frappe.db.get_value because i need only specific field and its lightweight. frappe.get_doc is heavier and retrieves the entire document.

### H1

frappe.call() is asynchronous, so its response is not immediate. Therefore, it should not be relied on inside validate() for synchronous validation. Use onload, refresh, or field-change handlers and process the response in the callback.

In DashPoint, assigned_rider uses frappe.call() to check the rider's zone against the delivery zone.

## J1 

A frappe.get_all() call can be placed directly inside a Jinja print template to fetch related data while rendering the print format.

For example:

```jinja
{% set zones = frappe.get_all("Delivery Zone", fields=["name", "zone_name"]) %} 


## K1 — Idempotent Scheduled Job

check_stuck_reattempts() runs daily and finds deliveries stuck in Re-attempt Scheduled for over 24 hours. It logs affected orders and emails the Ops Manager.

An Audit Log sentinel stuck_reattempt_check prevents duplicate execution on the same day.

**Test:** Ran the job twice; the sentinel count remained 1.

## K2 — N+1 Query

The original code calls frappe.get_doc() inside a loop, causing one Rider query per Delivery Order.

The fix collects all rider names, fetches the Riders in one bulk query, and creates a dictionary for lookup. This avoids the N+1 query pattern and reduces database calls.


## L1 

The standard Frappe REST API was tested with:

    GET /api/resource/Delivery%20Order/DO-2026-00007

When called without authentication, Frappe returned HTTP 403 because the Guest user does not have Delivery Order read permission.

The custom API get_delivery_status() reads delivery_order_name from frappe.form_dict and returns only:

1. status
2. zone
3. attempts_count

It does not expose the complete Delivery Order document or customer email.

For an existing Delivery Order, the API returned:

    {
        "status": "Re-attempt Scheduled",
        "zone": "South Zone",
        "attempts_count": 1
    }

For a non-existent Delivery Order, it returned:

    {
        "error": "Not found"
    }

with HTTP status 404.