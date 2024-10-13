
# creating own db to initialize this 


import sqlite3
from datetime import datetime

# Connect to the SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect('hotel_booking.db')
c = conn.cursor()

# Create Hotels table
c.execute('''
CREATE TABLE IF NOT EXISTS Hotels (
    hotel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_name TEXT NOT NULL,
    address TEXT,
    total_rooms INTEGER,
    phone TEXT
);
''')

# Create Rooms table
c.execute('''
CREATE TABLE IF NOT EXISTS Rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_id INTEGER,
    room_number INTEGER,
    room_type TEXT,
    price_per_day REAL,
    is_occupied BOOLEAN DEFAULT 0,
    FOREIGN KEY (hotel_id) REFERENCES Hotels(hotel_id)
);
''')

# Create Users table
c.execute('''
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT
);
''')

# Create Bookings table
c.execute('''
CREATE TABLE IF NOT EXISTS Bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER,
    user_id INTEGER,
    check_in_date TEXT,
    check_out_date TEXT,
    FOREIGN KEY (room_id) REFERENCES Rooms(room_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);
''')

# Commit the changes
conn.commit()

# Function to check room availability
def check_room_availability(hotel_id):
    c.execute('''
    SELECT * FROM Rooms
    WHERE hotel_id = ? AND is_occupied = 0;
    ''', (hotel_id,))
    available_rooms = c.fetchall()
    if available_rooms:
        print("Available rooms:", available_rooms)
    else:
        print("No available rooms in this hotel.")

# Function to book a room
def book_room(room_id, user_id, check_in_date, check_out_date):
    # Check if the room is available
    c.execute('''
    SELECT * FROM Rooms
    WHERE room_id = ? AND is_occupied = 0;
    ''', (room_id,))
    room = c.fetchone()
    
    if room:
        # Insert booking into Bookings table
        c.execute('''
        INSERT INTO Bookings (room_id, user_id, check_in_date, check_out_date)
        VALUES (?, ?, ?, ?);
        ''', (room_id, user_id, check_in_date, check_out_date))
        
        # Mark the room as occupied
        c.execute('''
        UPDATE Rooms
        SET is_occupied = 1
        WHERE room_id = ?;
        ''', (room_id,))
        
        # Commit the changes
        conn.commit()
        print(f"Room {room_id} successfully booked!")
    else:
        print("Room is already occupied or does not exist.")

# Function to calculate booking cost
def calculate_booking_cost(booking_id):
    c.execute('''
    SELECT (julianday(check_out_date) - julianday(check_in_date)) * r.price_per_day AS total_price
    FROM Bookings b
    JOIN Rooms r ON b.room_id = r.room_id
    WHERE b.booking_id = ?;
    ''', (booking_id,))
    
    total_price = c.fetchone()[0]
    print(f"Total booking cost: ${total_price:.2f}")

# Sample Data Insertion
def insert_sample_data():
    # Insert sample hotel
    c.execute('''
    INSERT INTO Hotels (hotel_name, address, total_rooms, phone)
    VALUES ('Sunset Hotel', '123 Ocean Drive', 10, '123-456-7890');
    ''')
    
    # Insert sample rooms
    c.execute('''
    INSERT INTO Rooms (hotel_id, room_number, room_type, price_per_day, is_occupied)
    VALUES (1, 101, 'Single', 100.0, 0),
           (1, 102, 'Double', 150.0, 0),
           (1, 103, 'Suite', 200.0, 0);
    ''')
    
    # Insert sample user
    c.execute('''
    INSERT INTO Users (name, email, phone)
    VALUES ('John Doe', 'john@example.com', '555-1234');
    ''')
    
    # Commit the changes
    conn.commit()

# Run sample data insertion
insert_sample_data()

# Check available rooms
check_room_availability(1)

# Book a room
book_room(1, 1, '2024-10-12', '2024-10-14')

# Calculate booking cost
calculate_booking_cost(1)

# Close the connection
conn.close()
