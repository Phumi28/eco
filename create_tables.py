import sqlite3

def create_tables():
    conn = sqlite3.connect('user_registration.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Create emissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vehicle_class TEXT NOT NULL,
            engine_size REAL NOT NULL,
            carbon_emission REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("Tables created successfully!")

if __name__ == '__main__':
    create_tables()
