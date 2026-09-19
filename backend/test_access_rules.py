from services.access_rules import verify_guest_access


print("\nEXPIRED BOOKING")
print("=" * 50)

expired = verify_guest_access(
    guest_id="gst_2631",
    booking_id="book_0014",
)

print(expired)


print("\nCURRENT BOOKING")
print("=" * 50)

current = verify_guest_access(
    guest_id="gst_2631",
    booking_id="book_demo_current_001",
)

print(current)