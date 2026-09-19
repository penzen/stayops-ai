from services.guests import get_guest
from services.reservations import get_reservation
from services.properties import get_property, get_access_system
from services.incidents import get_open_incidents


booking = get_reservation("book_0014")

print("\nBOOKING")
print(booking)

guest = get_guest(booking["guest_id"])

print("\nGUEST")
print(guest)

property_data = get_property(booking["property_id"])

print("\nPROPERTY")
print(property_data)

access = get_access_system(booking["property_id"])

print("\nACCESS")
print(access)

incidents = get_open_incidents(booking["property_id"])

print("\nOPEN INCIDENTS")
print(incidents)