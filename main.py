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
    cursor.execute("INSERT INTO Books (Name, Author, SerialNumber, Type, AddedDate) VALUES (%s, %s, %s, %s, %s)", (name, author, serial_number, book_type, added_date))
    conn.commit()
    conn.close()
    return f"Book '{name}' added successfully."

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
    cursor.execute("SELECT Name, AuthorID FROM books")
    books = cursor.fetchall()
    conn.close()
    # Returning the list of books with author 
    return {book['Name']: book['AuthorID'] for book in books} 

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
    choice = st.sidebar.radio("User Dashboard", ["Search Books", "Pay Fine"])
    # choice = st.selectbox("Choose an option", ["Search Books", "Pay Fine"])
    
    if choice == "Search Books":
        st.subheader("Search Books")
        
        book_names = get_book_names()
  
        selected_book = st.selectbox("Select a Book", book_names)
        
        if selected_book:
            st.write(f"You selected: **{selected_book}**")
            
            results = search_books(selected_book)
            
            if results:
                book = results[0] 
                author = get_author(book['AuthorID'])
                st.write(f"**Book Name**: {book['Name']}")
                st.write(f"**Author Name**: {author}")  
                st.write(f"**Serial Number**: {book['SerialNumber']}")
                st.write(f"**Type**: {book['Type']}")
                st.write(f"**Added Date**: {book['AddedDate']}")
            else:
                st.error("No details found for the selected book.")

    elif choice == "Pay Fine":
        st.subheader("Pay Fine")
        st.text("Processing Payment")

# admin dashboard
def admin_dashboard():
    st.title("Admin Dashboard")
    choice = st.sidebar.radio("Select Action", ["Add Book", "Issue Book", "Return Book", "Search Books"])

    if choice == "Add Book":
        st.subheader("Add Book")
        name = st.text_input("Book Name")
        author = st.text_input("Author")
        serial_number = st.text_input("Serial Number")
        book_type = st.selectbox("Type", ["Book", "Movie"])
        added_date = st.date_input("Added Date")
        if st.button("Add Book"):
            result = add_book(name, author, serial_number, book_type, added_date)
            st.success(result)
        
    elif choice == "Issue Book":
        st.subheader("Issue Book")
        book_dict = get_book_names()
        book_names = list(book_dict.keys())

        book_name = st.selectbox("Book Name", book_names)

        if "selected_author" not in st.session_state:
            st.session_state.selected_author = ""

        # Updating the author field when a book is selected
        if book_name:
            author_id = book_dict[book_name]
            st.session_state.selected_author = get_author(author_id)

        author_name = st.text_input("Author", value=st.session_state.selected_author, disabled=True)

        issue_date = st.date_input("Issue Date", min_value=datetime.today().date())
        return_date = st.date_input("Return Date", value=datetime.today().date() + timedelta(days=15))

        if st.button("Issue Book"):
            st.success(f"Book '{book_name}' issued successfully to {st.session_state.selected_author}.")

    elif choice == "Return Book":
        st.subheader("Return Book")
        book_dict = get_book_names()
        book_names = list(book_dict.keys())

        selected_book = st.selectbox("Book Name", book_names)

        if "return_author" not in st.session_state:
            st.session_state.return_author = ""

        if selected_book:
            author_id = book_dict[selected_book]
            st.session_state.return_author = get_author(author_id)

        author_name = st.text_input("Author", value=st.session_state.return_author, disabled=True)

        serial_number = st.text_input("Serial Number")
        return_date = st.date_input("Return Date", value=datetime.today().date())

        if st.button("Return Book"):
            st.success(f"Book '{selected_book}' by {st.session_state.return_author} returned successfully!")

    elif choice == "Search Books":
        st.subheader("Search Books")
        book_names = get_book_names()
  
        selected_book = st.selectbox("Select a Book", book_names)
        
        if selected_book:
            st.write(f"You selected: **{selected_book}**")
            
            results = search_books(selected_book)
            
            if results:
                book = results[0] 
                author = get_author(book['AuthorID'])
                st.write(f"**Book Name**: {book['Name']}")
                st.write(f"**Author Name**: {author}")  
                st.write(f"**Serial Number**: {book['SerialNumber']}")
                st.write(f"**Type**: {book['Type']}")
                st.write(f"**Added Date**: {book['AddedDate']}")
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

if __name__ == "__main__":
    main()
