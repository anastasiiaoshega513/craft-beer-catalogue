# 1. Empty cart formatting
# format_cart(None) should return an empty cart response.
# The response should contain id=None, an empty cart_items list, subtotal=0, and total=0.

# 2. Cart items formatting and totals
# format_cart() should include only valid cart items.
# Each item should contain id, beer_id, name, quantity, price, and image_url.
# subtotal should be calculated as price * quantity.
# total should include the delivery fee when the cart has at least one valid item.

# 3. Invalid cart item amounts
# format_cart() should ignore cart items with amount less than or equal to 0.
# If all cart items are ignored, subtotal and total should be 0.

# 4. Existing guest cookie
# get_or_create_guest_id() should return the existing guest_id from request cookies.
# It should not set a new cookie when guest_id already exists.

# 5. New guest cookie
# get_or_create_guest_id() should generate a new guest_id when the request has no guest_id cookie.
# It should set the guest_id cookie on the response with the expected cookie options.
# It should return the generated guest_id.
