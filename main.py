import streamlit as st
import mysql.connector
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
# import hashlib

load_dotenv() 

db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

# Database connection
def connect_db():
    return mysql.connector.connect(
        host=db_host,
        user=db_username,
        password=db_password,
        database=db_name
    )

def add_book(name, author, serial_number, book_type, added_date):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Check if the author exists
        cursor.execute("SELECT AuthorID FROM authors WHERE Name = %s", (author,))
        author_record = cursor.fetchone()

        if author_record:
            # Author exists, get their ID
            author_id = author_record[0]
        else:
            # Author does not exist, insert new author and get the ID
            cursor.execute("INSERT INTO authors (Name) VALUES (%s)", (author,))
            conn.commit()
            author_id = cursor.lastrowid  # Get the newly inserted author's ID

        # Insert the book entry into the Books table
        cursor.execute(
            "INSERT INTO Books (Name, AuthorID, SerialNumber, Type, AddedDate) VALUES (%s, %s, %s, %s, %s)",
            (name, author_id, serial_number, book_type, added_date)
        )

        conn.commit()
        return f"Book '{name}' added successfully with Serial Number '{serial_number}'."

    except Exception as e:
        conn.rollback()
        return f"Error adding book: {str(e)}"

    finally:
        cursor.close()
        conn.close()

from datetime import datetime

def issue_book(book_id, username, issue_date, return_date):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Get UserID from username
        cursor.execute("SELECT user_id FROM users WHERE fname = %s", (username,))
        user_record = cursor.fetchone()

        if not user_record:
            return f"Error: User '{username}' not found."

        user_id = user_record[0]

        # Check if the book is already issued (ReturnDate is NULL)
        cursor.execute(
            "SELECT * FROM IssuedBooks WHERE BookID = %s AND ReturnDate IS NULL",
            (book_id,)
        )
        issued_record = cursor.fetchone()

        if issued_record:
            return "Book is already issued and not yet returned."

        # If the book is available, proceed with issuing
        cursor.execute(
            "INSERT INTO IssuedBooks (BookID, UserID, IssueDate, ReturnDate) VALUES (%s, %s, %s, %s)",
            (book_id, user_id, issue_date, return_date)
        )
        
        conn.commit()
        return f"Book with ID {book_id} issued to '{username}' successfully."

    except Exception as e:
        conn.rollback()
        return f"Error issuing book: {str(e)}"

    finally:
        cursor.close()
        conn.close()


def get_all_books(show_issued=False):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)

    # Query to fetch all books with author details
    cursor.execute("""
        SELECT b.BookID, b.Name, a.Name AS Author, b.SerialNumber, b.Type, b.AddedDate, 
               (SELECT COUNT(*) FROM IssuedBooks ib WHERE ib.BookID = b.BookID AND ib.ReturnDate IS NULL) AS issued_status
        FROM books b
        JOIN authors a ON b.AuthorID = a.AuthorID
    """)
    
    books = cursor.fetchall()
    conn.close()

    if show_issued:
        # Return only books that are issued (issued_status > 0)
        return [book for book in books if book['issued_status'] > 0]
    return books  # Return all books if no filter is applied

def delete_book(book_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Check if the book is currently issued
        cursor.execute("SELECT * FROM IssuedBooks WHERE BookID = %s AND ReturnDate IS NULL", (book_id,))
        issued_record = cursor.fetchone()

        if issued_record:
            # If the book is issued, return an error message
            return "❌ Cannot delete: This book is currently issued and must be returned first."

        # If the book is not issued, proceed to delete
        cursor.execute("DELETE FROM Books WHERE BookID = %s", (book_id,))
        conn.commit()
        return "✅ Book deleted successfully."

    except mysql.connector.Error as e:
        # Rollback if there is an error and show the error message
        conn.rollback()
        return f"❌ Error deleting book: {str(e)}"

    finally:
        cursor.close()
        conn.close()


def get_author(author_id):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Name FROM authors WHERE AuthorID = %s", (author_id,))
    author = cursor.fetchone()
    conn.close()
    return author['Name'] if author else "Unknown Author"

def get_book_names():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch BookID, Name, and AuthorID
    cursor.execute("SELECT BookID, Name, AuthorID FROM books")
    books = cursor.fetchall()
    
    conn.close()
    
    # Returning a dictionary with BookID, Name, and AuthorID
    return {book['BookID']: {"Name": book['Name'], "AuthorID": book['AuthorID']} for book in books}

# searching for a book based on name
def search_books(name):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books WHERE Name LIKE %s", ("%" + name + "%",))
    books = cursor.fetchall()
    conn.close()
    return books

# user login 
def authenticate_user(email, password):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

# user dashboard
def user_dashboard():
    # st.title("User Dashboard")
    choice = st.sidebar.radio("User Dashboard", ["Search Books", "Pay Fine", "List All Books"])
    # choice = st.selectbox("Choose an option", ["Search Books", "Pay Fine"])

    if choice == "List All Books":
        st.subheader("List of All Books")
        
        # Toggle to filter issued books
        show_issued = st.checkbox("Show Only Issued Books")
        
        books = get_all_books(show_issued=show_issued)
        
        if books:
            # Prepare a list of dictionaries with the relevant book information
            book_data = []
            for book in books:
                issued_text = "✅ Available" if book['issued_status'] == 0 else "🚨 Issued"
                book_data.append({
                    "Book Name": book['Name'],
                    "Author": book['Author'],
                    "Serial Number": book['SerialNumber'],
                    "Type": book['Type'],
                    "Added Date": book['AddedDate'],
                    "Status": issued_text
                })
            
            # Display the data in a table format using st.dataframe()
            st.dataframe(book_data)
        else:
            st.warning("No books found matching the criteria.")

    elif choice == "Pay Fine":
        st.subheader("Pay Fine")
        st.text("Processing Payment")

    elif choice == "Search Books":
        st.subheader("Search Books")
        
        # Fetch books with their IDs and AuthorIDs
        book_dict = get_book_names()
        
        # Dropdown: Show book names but store selected BookID
        selected_book_id = st.selectbox("Select a Book", list(book_dict.keys()), format_func=lambda x: book_dict[x]["Name"])
        
        if selected_book_id:
            selected_book = book_dict[selected_book_id]  # Retrieve selected book details
            st.write(f"You selected: *{selected_book['Name']}*")

            # Search for the book using BookID instead of Name
            results = search_books(selected_book["Name"])
            
            if results:
                book = results[0]  
                author = get_author(book['AuthorID'])
                
                # Display book details
                st.write(f"📖 *Book Name*: {book['Name']}")
                st.write(f"✍ *Author Name*: {author}")  
                st.write(f"🔢 *Serial Number*: {book['SerialNumber']}")
                st.write(f"📚 *Type*: {book['Type']}")
                st.write(f"📅 *Added Date*: {book['AddedDate']}")
            else:
                st.error("No details found for the selected book.")


    elif choice == "Pay Fine":
        st.subheader("Pay Fine")
        st.text("Processing Payment")

def get_usernames():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT fname FROM users WHERE role = 'user'")  # Exclude admins
    users = cursor.fetchall()
    conn.close()
    return [user["fname"] for user in users]

# admin dashboard
def admin_dashboard():
    st.title("Admin Dashboard")
    choice = st.sidebar.radio("Select Action", ["Add Book", "Issue Book", "Return Book", "Search Books", "List All Books", "Delete Book"])
    if choice == "List All Books":
        st.subheader("List of All Books")
        
        # Toggle to filter issued books
        show_issued = st.checkbox("Show Only Issued Books")
        
        books = get_all_books(show_issued=show_issued)
        
        if books:
            # Prepare a list of dictionaries with the relevant book information
            book_data = []
            for book in books:
                issued_text = "✅ Available" if book['issued_status'] == 0 else "🚨 Issued"
                book_data.append({
                    "Book Name": book['Name'],
                    "Author": book['Author'],
                    "Serial Number": book['SerialNumber'],
                    "Type": book['Type'],
                    "Added Date": book['AddedDate'],
                    "Status": issued_text
                })
            
            # Display the data in a table format using st.dataframe()
            st.dataframe(book_data)
        else:
            st.warning("No books found matching the criteria.")

    
    elif choice == "Add Book":
        st.subheader("Add Book")
        
        name = st.text_input("Book Name")
        author = st.text_input("Author")
        serial_number = st.text_input("Serial Number")
        book_type = st.selectbox("Type", ["Book", "Movie"])
        added_date = st.date_input("Added Date")

        if st.button("Add Book"):
            result = add_book(name, author, serial_number, book_type, added_date)
            st.success(result)

    elif choice == "Delete Book":
        st.subheader("Delete Book")

        # Fetch books with their IDs
        book_dict = get_book_names()

        # Dropdown: Show book names but select by BookID
        selected_book_id = st.selectbox("Select a Book to Delete", list(book_dict.keys()), format_func=lambda x: book_dict[x]["Name"])

        if selected_book_id:
            selected_book = book_dict[selected_book_id]  # Retrieve book details
            st.write(f"⚠ You are about to delete *{selected_book['Name']}* by {get_author(selected_book['AuthorID'])}.")

            # Confirm before deleting
            if st.button("Delete Book"):
                result = delete_book(selected_book_id)
                st.success(result)
   
    elif choice == "Issue Book":
    
        st.subheader("Issue Book")

        # Fetch books with their IDs and AuthorIDs
        book_dict = get_book_names()

        # Dropdown: Show book names but store selected BookID
        selected_book_id = st.selectbox("Select a Book", list(book_dict.keys()), format_func=lambda x: book_dict[x]["Name"])

        if "selected_author" not in st.session_state:
            st.session_state.selected_author = ""

        # Updating the author field when a book is selected
        if selected_book_id:
            selected_book = book_dict[selected_book_id]
            author_id = selected_book["AuthorID"]
            st.session_state.selected_author = get_author(author_id)

        # Display the author name (disabled field)
        author_name = st.text_input("Author", value=st.session_state.selected_author, disabled=True)

        # Admin selects a user (username)
        usernames = get_usernames()
        selected_username = st.selectbox("Select User to Issue", usernames)

        # Other input fields
        issue_date = st.date_input("Issue Date", min_value=datetime.today().date())
        return_date = st.date_input("Return Date", value=datetime.today().date() + timedelta(days=15))

        if st.button("Issue Book"):
            result = issue_book(selected_book_id, selected_username, issue_date, return_date)
            st.success(result)


    elif choice == "Return Book":
        st.subheader("Return Book")

        # Fetch books with their IDs and AuthorIDs
        book_dict = get_book_names()

        # Dropdown: Show book names but store selected BookID
        selected_book_id = st.selectbox("Select a Book", list(book_dict.keys()), format_func=lambda x: book_dict[x]["Name"])

        if "return_author" not in st.session_state:
            st.session_state.return_author = ""

        # Updating the author field when a book is selected
        if selected_book_id:
            selected_book = book_dict[selected_book_id]
            author_id = selected_book["AuthorID"]
            st.session_state.return_author = get_author(author_id)

        # Display the author name (disabled field)
        author_name = st.text_input("Author", value=st.session_state.return_author, disabled=True)

        # Other input fields
        serial_number = st.text_input("Serial Number")
        return_date = st.date_input("Return Date", value=datetime.today().date())

        if st.button("Return Book"):
            # Replace missing function call with actual return_book function
            user_id = st.session_state.get("user_id", None)  # Assuming user_id is stored in session state
            if user_id:
                result = return_book(selected_book_id, user_id, return_date)
                st.success(result)
            else:
                st.error("User not logged in. Please log in to return a book.")


    elif choice == "Search Books":
        st.subheader("Search Books")

        # Fetch books with their IDs and AuthorIDs
        book_dict = get_book_names()

        # Dropdown: Show book names but store selected BookID
        selected_book_id = st.selectbox("Select a Book", list(book_dict.keys()), format_func=lambda x: book_dict[x]["Name"])

        if selected_book_id:
            selected_book = book_dict[selected_book_id]  # Retrieve selected book details
            st.write(f"You selected: *{selected_book['Name']}*")

            # Search for the book using BookID instead of Name
            results = search_books(selected_book["Name"])

            if results:
                book = results[0]  
                author = get_author(book['AuthorID'])

                # Display book details
                st.write(f"📖 *Book Name*: {book['Name']}")
                st.write(f"✍ *Author Name*: {author}")  
                st.write(f"🔢 *Serial Number*: {book['SerialNumber']}")
                st.write(f"📚 *Type*: {book['Type']}")
                st.write(f"📅 *Added Date*: {book['AddedDate']}")
            else:
                st.error("No details found for the selected book.")


    elif choice == "Pay Fine":
        st.subheader("Pay Fine")
        st.text("Processing payment.")

# Main function - 
def main():
    st.title("Library Management System")

    # Login Form -
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.subheader("User Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            user = authenticate_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_role = user['role']
                st.session_state.user_name = user['fname']
                st.success(f"Welcome, {user['fname']}!")
            else:
                st.error("Invalid email or password. Please try again.")
    else:
        st.sidebar.write(f"Logged in as: {st.session_state.user_name}")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False

        if st.session_state.user_role == "admin":
            admin_dashboard()
        else:
            user_dashboard()

if _name_ == "_main_":
    main()
