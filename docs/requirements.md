# Shared shop requirements — initial baseline, before any bugs
R1: Search is case-insensitive, ignores outer spaces, and shows matching product names; no match displays “No products found.”
R2: Adding the same product twice gives quantity 2, without duplicate cart rows.
R3: Quantity must be an integer from 1 to 99; invalid updates retain the previous quantity.
R4: Subtotals and total equal displayed unit price × quantity; no fees or discounts.
R5: Removing a product removes its row and updates the total.
R6: Empty-cart checkout is rejected with a message.
R7: Checkout requires a syntactically valid email; invalid input cannot place an order.
R8: Valid nonempty checkout shows confirmation and empties the cart; no real payment.
Synthetic catalog: Headphones £20.00, Keyboard £30.00, Mouse £10.00.
