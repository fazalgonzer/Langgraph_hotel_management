import sqlite3
from datetime import date, datetime
from typing import Optional
from langchain.tools import tool
import pytz
from langchain_core.runnables import RunnableConfig
from langchain.vectorstores import FAISS

from langchain_community.embeddings import HuggingFaceEmbeddings
db = 'hotel_booking.db'  # Replace with your actual database name


@tool
def fetch_user_hotel_information(config: RunnableConfig) -> list[dict]:
    """Fetch all hotel bookings for the user along with corresponding hotel information."""
    configuration = config.get("configurable", {})
    user_id = configuration.get("user_id", None)  # Updated to use user_id
    if not user_id:
        raise ValueError("No user ID configured.")

    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = """
    SELECT 
        b.booking_id, b.check_in_date, b.check_out_date, 
        h.hotel_id, h.hotel_name, 
    FROM 
        Bookings b
        JOIN hotels h ON b.hotel_id = h.hotel_id
    WHERE 
        b.user_id = ?  -- Updated to filter by user_id
    """
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]
    results = [dict(zip(column_names, row)) for row in rows]

    cursor.close()
    conn.close()

    return results


@tool
def update_hotel_booking(
    booking_id: str, new_check_in_date: date, new_check_out_date: date, *, config: RunnableConfig
) -> str:
    """Update the user's hotel booking to new dates."""
    configuration = config.get("configurable", {})
    user_id = configuration.get("user_id", None)  # Updated to use user_id
    if not user_id:
        raise ValueError("No user ID configured.")

    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT hotel_id FROM Bookings WHERE booking_id = ?", (booking_id,)
    )
    existing_booking = cursor.fetchone()
    if not existing_booking:
        cursor.close()
        conn.close()
        return "Invalid booking ID provided."

    # Check if the user actually has this booking
    cursor.execute(
        "SELECT * FROM Bookings WHERE booking_id = ? AND user_id = ?",  # Updated to check by user_id
        (booking_id, user_id),
    )
    current_booking = cursor.fetchone()
    if not current_booking:
        cursor.close()
        conn.close()
        return f"Current signed-in user with ID {user_id} not the owner of booking {booking_id}"

    # Update the booking with new dates
    cursor.execute(
        "UPDATE Bookings SET check_in_date = ?, check_out_date = ? WHERE booking_id = ?",
        (new_check_in_date, new_check_out_date, booking_id),
    )
    conn.commit()

    cursor.close()
    conn.close()
    return "Booking successfully updated."

#
@tool
def cancel_hotel_booking(booking_id: str, *, config: RunnableConfig) -> str:
    """Cancel the user's hotel booking and remove it from the database."""
    configuration = config.get("configurable", {})
    user_id = configuration.get("user_id", None)  # Updated to use user_id
    if not user_id:
        raise ValueError("No user ID configured.")

    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT hotel_id FROM Bookings WHERE booking_id = ?", (booking_id,)
    )
    existing_booking = cursor.fetchone()
    if not existing_booking:
        cursor.close()
        conn.close()
        return "No existing booking found for the given booking ID."

    # Check if the user actually has this booking
    cursor.execute(
        "SELECT hotel_id FROM Bookings WHERE booking_id = ? AND user_id = ?",  # Updated to check by user_id
        (booking_id, user_id),
    )
    current_booking = cursor.fetchone()
    if not current_booking:
        cursor.close()
        conn.close()
        return f"Current signed-in user with ID {user_id} not the owner of booking {booking_id}"

    # Delete the booking from the database
    cursor.execute("DELETE FROM Bookings WHERE booking_id = ?", (booking_id,))
    conn.commit()

    cursor.close()
    conn.close()
    return "Booking successfully cancelled."











# display a a room avaialbe so we can book it 
@tool
def display_available_rooms() ->list[str]:
    """Fetch and display all available rooms from the database."""
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = """
    SELECT 
        room_id, room_type, price_per_night, is_occupied 
    FROM 
        Rooms 
    WHERE 
        is_occupied = 1  -- Assuming 1 means available
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    column_names = [column[0] for column in cursor.description]

    # Print header
    print("Available Rooms:")
    print("-" * 40)
    print(f"{' | '.join(column_names)}")
    print("-" * 40)
    res=[]
    # Print each room's details
    for row in rows:
        room_details = ' | '.join(str(value) for value in row)
        res.append(room_details)
    


    cursor.close()
    conn.close()
    return res







@tool
def create_room_booking(room_number: str, check_in_date: str, check_out_date: str, *, config: RunnableConfig) -> str:
    """Create a booking for a specific room."""
    configuration = config.get("configurable", {})
    user_id = configuration.get("user_id", None)
    
    if not user_id:
        raise ValueError("No user ID configured.")
    
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Check if the room is available
    cursor.execute(
        "SELECT room_id, is_occupied FROM Rooms WHERE room_number = ?",
        (room_number,)
    )
    room = cursor.fetchone()

    if not room or room[1] != 1:  # Assuming 1 means available
        cursor.close()
        conn.close()
        return f"Room {room_number} is not available for booking."

    room_id = room[0]

    # Insert booking into the Bookings table
    cursor.execute(
        "INSERT INTO Bookings (user_id, room_id, check_in_date, check_out_date) VALUES (?, ?, ?, ?)",
        (user_id, room_id, check_in_date, check_out_date)
    )
    conn.commit()

    # Update the room's availability
    cursor.execute(
        "UPDATE Rooms SET is_occupied = 0 WHERE room_id = ?",
        (room_id,)
    )
    conn.commit()

    cursor.close()
    conn.close()

    return f"Booking created successfully for Room {room_number} from {check_in_date} to {check_out_date}."



#lookup policy


@tool
def lookup_policy(query: str) -> str:
    """Consult the company policies to check whether certain options are permitted.
    Use this before making any flight changes performing other 'write' events."""
    retriver=FAISS.load_local('faiss.index',embeddings=HuggingFaceEmbeddings(),allow_dangerous_deserialization=True)
    docs = retriver.similarity_search(
    query,
    k=3)
    res=[]
    for r in docs:
              res.append(r.page_content)
    return docs 