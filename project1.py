import mysql.connector
import getpass

class FlightManagement:
    def __init__(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="flightdb",
            auth_plugin="mysql_native_password"
        )
        self.cursor = self.db.cursor()
        self.admin_user = "admin"
        self.admin_pass = "admin123"
        self.current_user = None
        self.create_tables()

    def create_tables(self):
        # Users table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            password VARCHAR(100)
        )""")
        # Flights table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            id INT AUTO_INCREMENT PRIMARY KEY,
            origin VARCHAR(100),
            destination VARCHAR(100),
            departure_date DATE,
            seats INT
        )""")
        # Bookings table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            flight_id INT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE
        )""")
        self.db.commit()

    def register(self):
        name = input("Name: ")
        email = input("Email: ")
        if "@" not in email:
            print("Invalid email")
            return
        self.cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if self.cursor.fetchone():
            print("Email already registered")
            return
        password = getpass.getpass("Create password: ")
        self.cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        self.db.commit()
        print("Registration successful")

    def login(self):
        email = input("Email: ")
        password = getpass.getpass("Password: ")
        # Check for admin
        if email == self.admin_user and password == self.admin_pass:
            print("Welcome, Admin")
            self.admin_menu()
            return
        # Check for normal user
        self.cursor.execute(
            "SELECT id, name FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        result = self.cursor.fetchone()
        if result:
            self.current_user = {
                'id': result[0],
                'name': result[1]
            }
            print(f"Welcome, {result[1]}")
            self.user_menu()
        else:
            print("Invalid credentials")

    def admin_menu(self):
        while True:
            print("\n1.Add Flight\n2.Delete Flight\n3.View Flights\n4.View Bookings\n5.View Users\n6.Logout")
            choice = input("Choice: ")
            if choice == "1":
                self.add_flight()
            elif choice == "2":
                self.delete_flight()
            elif choice == "3":
                self.view_flights()
            elif choice == "4":
                self.view_bookings()
            elif choice == "5":
                self.view_users()
            elif choice == "6":
                break
            else:
                print("Invalid choice")

    def user_menu(self):
        while True:
            print("\n1.View Flights\n2.Book Flight\n3.Cancel Booking\n4.Logout")
            choice = input("Choice: ")
            if choice == "1":
                self.view_flights()
            elif choice == "2":
                self.book_flight()
            elif choice == "3":
                self.cancel_booking()
            elif choice == "4":
                self.current_user = None
                break
            else:
                print("Invalid choice")

    def add_flight(self):
        origin = input("Origin: ")
        destination = input("Destination: ")
        date = input("Departure Date (YYYY-MM-DD): ")
        seats = input("Number of seats: ")
        if not seats.isdigit():
            print("Seats must be a number")
            return
        self.cursor.execute(
            "INSERT INTO flights (origin, destination, departure_date, seats) VALUES (%s, %s, %s, %s)",
            (origin, destination, date, int(seats))
        )
        self.db.commit()
        print("Flight added successfully")

    def delete_flight(self):
        self.view_flights()
        flight_id = input("Enter flight ID to delete: ")
        if not flight_id.isdigit():
            print("Invalid ID")
            return
        self.cursor.execute("DELETE FROM flights WHERE id=%s", (int(flight_id),))
        self.db.commit()
        print("Flight deleted")

    def view_flights(self):
        self.cursor.execute("SELECT id, origin, destination, departure_date, seats FROM flights")
        flights = self.cursor.fetchall()
        if not flights:
            print("No flights available")
            return
        print("ID | Origin -> Destination | Date | Seats")
        for f in flights:
            print(f"{f[0]} | {f[1]} -> {f[2]} | {f[3]} | {f[4]}")

    def view_users(self):
        self.cursor.execute("SELECT id, name, email FROM users")
        for u in self.cursor.fetchall():
            print(f"{u[0]} | {u[1]} | {u[2]}")

    def view_bookings(self):
        self.cursor.execute(
            "SELECT b.id, u.name, f.origin, f.destination, f.departure_date FROM bookings b "
            "JOIN users u ON b.user_id=u.id "
            "JOIN flights f ON b.flight_id=f.id"
        )
        bookings = self.cursor.fetchall()
        if not bookings:
            print("No bookings found")
            return
        print("BookingID | User | Flight (Origin->Destination) | Date")
        for b in bookings:
            print(f"{b[0]} | {b[1]} | {b[2]}->{b[3]} | {b[4]}")

    def book_flight(self):
        self.view_flights()
        flight_id = input("Enter flight ID to book: ")
        if not flight_id.isdigit():
            print("Invalid ID")
            return
        # Check seats
        self.cursor.execute("SELECT seats FROM flights WHERE id=%s", (int(flight_id),))
        row = self.cursor.fetchone()
        if not row:
            print("Flight not found")
            return
        seats = row[0]
        if seats <= 0:
            print("No seats available")
            return
        # Book
        self.cursor.execute(
            "INSERT INTO bookings (user_id, flight_id) VALUES (%s, %s)",
            (self.current_user['id'], int(flight_id))
        )
        self.cursor.execute(
            "UPDATE flights SET seats=seats-1 WHERE id=%s", (int(flight_id),)
        )
        self.db.commit()
        print("Flight booked successfully")

    def cancel_booking(self):
        # Show user bookings
        self.cursor.execute(
            "SELECT b.id, f.origin, f.destination, f.departure_date FROM bookings b "
            "JOIN flights f ON b.flight_id=f.id "
            "WHERE b.user_id=%s", (self.current_user['id'],)
        )
        bookings = self.cursor.fetchall()
        if not bookings:
            print("You have no bookings")
            return
        print("BookingID | Origin->Destination | Date")
        for b in bookings:
            print(f"{b[0]} | {b[1]}->{b[2]} | {b[3]}")
        bid = input("Enter Booking ID to cancel: ")
        if not bid.isdigit():
            print("Invalid ID")
            return
        # Get flight id before deleting
        self.cursor.execute("SELECT flight_id FROM bookings WHERE id=%s AND user_id=%s", (int(bid), self.current_user['id']))
        row = self.cursor.fetchone()
        if not row:
            print("Booking not found")
            return
        flight_id = row[0]
        # Cancel booking
        self.cursor.execute("DELETE FROM bookings WHERE id=%s", (int(bid),))
        # Restore seat
        self.cursor.execute("UPDATE flights SET seats=seats+1 WHERE id=%s", (flight_id,))
        self.db.commit()
        print("Booking canceled successfully")

    def home(self):
        while True:
            print("\n1.Register\n2.Login\n3.Exit")
            choice = input("Choice: ")
            if choice == "1":
                self.register()
            elif choice == "2":
                self.login()
            elif choice == "3":
                break
            else:
                print("Invalid choice")

if __name__ == '__main__':
    app = FlightManagement()
    app.home()

