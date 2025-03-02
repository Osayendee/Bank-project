import sqlite3
import hashlib
import random
from getpass import getpass

# Connect to SQLite Database
conn = sqlite3.connect("banking.db")
cursor = conn.cursor()

# Create Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    age INTEGER NOT NULL,
    password TEXT NOT NULL
)
""")

# Create Accounts Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    account_num INTEGER UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    balance REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (account_num),
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")

# Create Transactions Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    recipient_account INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
""")

conn.commit()

# Generate Unique Account Number
def generate_account_number():
    while True:
        account_number = random.randint(100000, 999999)
        cursor.execute("SELECT 1 FROM accounts WHERE account_num = ?", (account_number,))
        if cursor.fetchone() is None:
            return account_number

# Create Bank Account for New Users
def create_bank_account(user_id):
    cursor.execute("SELECT account_num FROM accounts WHERE user_id = ?", (user_id,))
    existing_account = cursor.fetchone()

    if existing_account:
        return existing_account[0]

    account_number = generate_account_number()
    cursor.execute("INSERT INTO accounts (account_num, user_id, balance) VALUES (?, ?, 0.0)", 
                   (account_number, user_id))
    conn.commit()
    
    return account_number

# Transaction History
def transaction_history(user_id):
    cursor.execute("SELECT type, amount, recipient_account, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    transactions = cursor.fetchall()

    if not transactions:
        print("No transaction history available.")
        return

    print("\n*************** Transaction History ***************")
    for t in transactions:
        txn_type, amount, recipient, timestamp = t
        if txn_type == "Transfer":
            print(f"{timestamp}: {txn_type} of ${amount:.2f} to Account {recipient}")
        else:
            print(f"{timestamp}: {txn_type} of ${amount:.2f}")
    print("**************************************************")

# Transfer Money
def transfer_money(user_id):
    sender_acc = cursor.execute("SELECT account_num, balance FROM accounts WHERE user_id = ?", (user_id,)).fetchone()
    
    if not sender_acc:
        print("You don't have a bank account.")
        return
    
    sender_acc_num, sender_balance = sender_acc

    try:
        recipient_acc_num = int(input("Enter recipient's account number: "))
        amount = float(input("Enter amount to transfer: "))

        if amount <= 0:
            print("Transfer amount must be greater than zero.")
            return
        if sender_balance < amount:
            print("Insufficient balance!")
            return

    except ValueError:
        print("Invalid input! Enter valid numbers.")
        return

    recipient = cursor.execute("SELECT user_id FROM accounts WHERE account_num = ?", (recipient_acc_num,)).fetchone()
    
    if not recipient:
        print("Recipient account number not found.")
        return
    
    recipient_id = recipient[0]

    # Perform the transaction
    cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, recipient_id))
    
    # Log transaction
    cursor.execute("INSERT INTO transactions (user_id, type, amount, recipient_account) VALUES (?, 'Transfer', ?, ?)", 
                   (user_id, amount, recipient_acc_num))
    conn.commit()

    print(f"Successfully transferred ${amount:.2f} to Account {recipient_acc_num}.")

# Account Details
def view_account_details(user_id):
    cursor.execute("""
    SELECT users.first_name, users.last_name, users.username, accounts.account_num 
    FROM users JOIN accounts ON users.id = accounts.user_id 
    WHERE users.id = ?
    """, (user_id,))
    
    user = cursor.fetchone()
    
    if user:
        print("\n*************** Account Details ***************")
        print(f"Full Name: {user[0]} {user[1]}")
        print(f"Username: {user[2]}")
        print(f"Account Number: {user[3]}")
        print("**************************************************")
    else:
        print("Account details not found.")

# Deposit Money
def deposit_money(user_id):
    try:
        amount = float(input("Enter amount to deposit: "))
        if amount <= 0:
            print("Deposit amount must be greater than zero.")
            return
    except ValueError:
        print("Invalid input! Enter a valid number.")
        return

    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    cursor.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, 'Deposit', ?)", 
                   (user_id, amount))
    conn.commit()

    print(f"Successfully deposited ${amount:.2f}.")

# Withdraw Money
def withdraw_money(user_id):
    cursor.execute("SELECT balance FROM accounts WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    try:
        amount = float(input("Enter amount to withdraw: "))
        if amount <= 0:
            print("Withdrawal amount must be greater than zero.")
            return
        if balance < amount:
            print("Insufficient balance!")
            return
    except ValueError:
        print("Invalid input! Enter a valid number.")
        return

    cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    cursor.execute("INSERT INTO transactions (user_id, type, amount) VALUES (?, 'Withdrawal', ?)", 
                   (user_id, amount))
    conn.commit()

    print(f"Successfully withdrew ${amount:.2f}.")

# View Account Balance
def view_account(user_id):
    cursor.execute("SELECT account_num, balance FROM accounts WHERE user_id = ?", (user_id,))
    account = cursor.fetchone()

    if account:
        print("\n*************** Account Balance ***************")
        print(f"Account Number: {account[0]}")
        print(f"Balance: ${account[1]:.2f}")
        print("************************************************")
    else:
        print("You don't have an account yet. Please contact support.")

# Sign Up
def sign_up():
    print("\n*************** Sign Up ***************")

    first_name = input("Enter your first name: ").strip()
    if not first_name:
        print("First name cannot be blank.")
        return

    last_name = input("Enter your last name: ").strip()
    if not last_name:
        print("Last name cannot be blank.")
        return

    username = input("Enter your username: ").strip()
    if not username:
        print("Username cannot be blank.")
        return

    try:
        age = int(input("Enter your age: "))
        if age < 18:
            print("You must be at least 18 years old to register.")
            return
    except ValueError:
        print("Age must be a number.")
        return

    password = getpass("Enter your password: ").strip()
    if not password:
        print("Password cannot be blank.")
        return

    confirm_password = getpass("Confirm your password: ").strip()
    if password != confirm_password:
        print("Passwords do not match.")
        return

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute("""
        INSERT INTO users (first_name, last_name, username, age, password) 
        VALUES (?, ?, ?, ?, ?)
        """, (first_name, last_name, username, age, hashed_password))
        conn.commit()

        user_id = cursor.lastrowid
        print(f"User successfully registered! (Username: {username})")

        # Create bank account for the new user
        create_bank_account(user_id)

        print("You can now log in.")
        log_in()
    except sqlite3.IntegrityError:
        print("Username already exists. Try a different one.")

# Log In
def log_in():
    print("\n*************** Log In ***************")

    username = input("Enter your username: ").strip()
    if not username:
        print("Username cannot be blank.")
        return

    password = getpass("Enter your password: ").strip()
    if not password:
        print("Password cannot be blank.")
        return

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    user = cursor.execute("""
    SELECT id, first_name FROM users WHERE username = ? AND password = ?
    """, (username, hashed_password)).fetchone()

    if user is None:
        print("Invalid username or password.")
        return

    print(f"Log-in successful! Welcome, {user[1]}!")
    
    # Ensure user has an account
    create_bank_account(user[0])
    
    checkout(user)

# Banking Menu
def checkout(user):
    while True:
        print("\n*************** Banking Menu ***************")
        print("1. View Account Details")
        print("2. View Account Balance")
        print("3. Deposit Money")
        print("4. Withdraw Money")
        print("5. Transfer Money")
        print("6. View Transaction History")
        print("7. Log Out")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            view_account_details(user[0])
        elif choice == "2":
            view_account(user[0])
        elif choice == "3":
            deposit_money(user[0])
        elif choice == "4":
            withdraw_money(user[0])
        elif choice == "5":
            transfer_money(user[0])
        elif choice == "6":
            transaction_history(user[0])
        elif choice == "7":
            print("Logging out...")
            break
        else:
            print("Invalid choice! Please try again.")

# Main Menu System
menu = """
*************** Banking System ***************
1. Sign Up
2. Log In
3. Quit
"""

try:
    while True:
        print(menu)
        choice = input("Choose an option from the menu above: ").strip()

        if choice == "1":
            sign_up()
        elif choice == "2":
            log_in()
        elif choice == "3":
            print("Thanks for using FK'S BANK!")
            break
        else:
            print("Invalid choice, please select from the menu.")
except Exception as e:
    print(f"Something went wrong: {e}")
finally:
    print("Closing database connection.")
    conn.close()