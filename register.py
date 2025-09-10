import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from tkcalendar import DateEntry
import re
import sqlite3

def validName(name):
    return bool(re.fullmatch(r"[A-Za-zÁ-ÿ\s]+", name))

def initializeDatabase():
    with sqlite3.connect("registrations.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                birth_date DATE NOT NULL,
                registration_date TIMESTAMP NOT NULL         
                )
         """)
        
def saveInDatabase(name, lastname, age, registration_date):
    with sqlite3.connect("registrations.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registrations (name, last_name, birth_date, registration_date)
            VALUES (?, ?, ?, ?)
         """, (name, lastname, age, registration_date))

def savedata():
    name = entry_name.get().strip()
    lastname = entry_lastname.get().strip()
    age = birthDate.get_date()
    selectedYear = age.year
    cadastreDate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if name and lastname and age:
        if not validName(name):
            messagebox.showerror("Error", "The 'Name' field must contain only letters and spaces.")
            entry_name.delete(0, tk.END)
            return

        if not validName(lastname):
            messagebox.showerror("Error", "The 'Last name' field must contain only latters and spaces.")
            entry_lastname.delete(0, tk.END)
            return
        
        if ((datetime.now().year - selectedYear) - ((datetime.now().month, datetime.now().day) < (age.month, age.day))) < 18:
                messagebox.showwarning("Error", "You need to be 18 years old or over to register.")
                birthDate.set_date(datetime.today())
                return
        
        try:
            saveInDatabase(name, lastname, age, cadastreDate)
            messagebox.showinfo("Success","Registration completed successfully!")
            entry_name.delete(0, tk.END)
            entry_lastname.delete(0, tk.END)
            birthDate.set_date(datetime.today())
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"Error to saving data: {error}.")
    else:
        messagebox.showerror("Error", "There are empty fields.")
        return

def showData():
    dataWindow = tk.Toplevel(app)
    dataWindow.title("Database")
    dataWindow.geometry("600x400")

    tree = ttk.Treeview(dataWindow, columns=("ID", "Name", "Last Name", "Birth Date", "Registration Date"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Name", text="Name")
    tree.heading("Last Name", text="Last Name")
    tree.heading("Birth Date", text="Birth Date")
    tree.heading("Registration Date", text="Registration Date")
    tree.pack(fill=tk.BOTH, expand=True)

    with sqlite3.connect("registrations.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registrations")
        rows = cursor.fetchall()
        for row in rows:
            tree.insert("",tk.END, values=row)

    search_frame = tk.Frame(dataWindow)
    search_frame.pack(fill=tk.X, pady=5)
    tk.Label(search_frame, text="Search: ").pack(side=tk.LEFT, padx=5)
    search_entry= tk.Entry(search_frame)
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    def searchData(query):
        tree.selection_remove(tree.selection())

        with sqlite3.connect("registrations.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM registrations WHERE name LIKE ? OR last_name LIKE ?", (f"%{query}", f"%{query}")) 
            rows = cursor.fetchall()
        
        if not rows:
            messagebox.showinfo("Error", "No record found.")
            return

        for row in tree.get_children():
            tree.delete(row)

        for row in rows:
            tree.insert("", tk.END, values=row)
            tree.selection_add(tree.get_children()[-1])
            tree.focus(tree.get_children()[-1])

    def editData(tree):
        selectedData = tree.selection()
        if not selectedData:
            messagebox.showerror("Error", "No record selected.")
            dataWindow.lift()
            return
        
        record = tree.item(selectedData)
        recordID, name, last_name, birth_date, reg_date = record['values']

        editWindow = tk.Toplevel(app)
        editWindow.title("Edit Data")
        editWindow.geometry("400x300")
        editWindow.grab_set()

        tk.Label(editWindow, text="Name: ").pack(pady=5)
        editName = tk.Entry(editWindow)
        editName.pack(pady=5)
        editName.insert(0, name)

        tk.Label(editWindow, text="Last Name: ").pack(pady=5)
        editLastName = tk.Entry(editWindow)
        editLastName.pack(pady=5)
        editLastName.insert(0, last_name)

        tk.Label(editWindow, text="Birth Date: ").pack(pady=5)
        editBirthDate = DateEntry(editWindow, width=16, background="gray", foreground="white", date_pattern="yyyy-mm-dd")
        editBirthDate.pack(pady=5)
        editBirthDate.set_date(birth_date) 

        def saveChanges():
            newName = editName.get().strip()
            newLastName = editLastName.get().strip()
            newBirthDate = editBirthDate.get_date()

            if not validName(newName) or not validName(newLastName):
                messagebox.showerror("Error", "'Name' and 'Last Name' must contain only letters and spaces.")
                return

            if ((datetime.now().year - newBirthDate.year) - ((datetime.now().month, datetime.now().day) < (newBirthDate.month, newBirthDate.day))) < 18:
                messagebox.showwarning("Error", "User must be 18 years or older.")
                return

            try:
                with sqlite3.connect("registrations.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    UPDATE registrations SET name = ?,
                    last_name = ?,
                    birth_date = ?
                    WHERE id = ? 
                    """, (newName, newLastName, newBirthDate, recordID))
                    conn.commit()
                messagebox.showinfo("Success", "Record updated successfully.")
                editWindow.destroy()
                dataWindow.destroy()
                showData()
            except sqlite3.Error as error:
                messagebox.showerror("Error", f"Error updating record: {error}")
            
        saveChangesButton = tk.Button(editWindow, text="Save Changes", command=saveChanges)
        saveChangesButton.pack(pady=10)

    def deleteData():
        selectedData = tree.selection()
        if not selectedData:
            messagebox.showerror("Error", "No record selected.")
            dataWindow.lift()
            dataWindow.grab_set()
            return

        record = tree.item(selectedData)
        recordID = record['values'][0]

        try:
            with sqlite3.connect("registrations.db") as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM registrations WHERE id = ?", (recordID,))
                conn.commit()

            tree.delete(selectedData)
            dataWindow.lift()
            dataWindow.grab_set()
            messagebox.showinfo("Success", "Record deleted successfully.")
        except sqlite3.Error as error:
            messagebox.showerror("Error", f"Error deleting record: {error}.")

    editButton = tk.Button(dataWindow, text="Edit Selected", command=lambda:editData(tree))
    editButton.pack(pady=10)
    
    deleteButton = tk.Button(dataWindow, text="Delete Selected", command=deleteData)
    deleteButton.pack(pady=10)

    searchButton = tk.Button(search_frame, text="Search", command= lambda:searchData(search_entry.get()))
    searchButton.pack(side=tk.LEFT,padx=5)

    closeButton = tk.Button(dataWindow, text="Close", command=dataWindow.destroy)
    closeButton.pack(pady=10)

def cancel():
    messagebox.showinfo("Cancel","Operation canceled.")
    app.destroy()

initializeDatabase()

app = tk.Tk()
app.title("Register system")
app.geometry("700x500")

lable_name = tk.Label(app, text="Name: ")
lable_name.pack(pady=5)
entry_name = tk.Entry(app)
entry_name.pack(pady=5)

lable_lastname = tk.Label(app, text="Last name: ")
lable_lastname.pack(pady=5)
entry_lastname = tk.Entry(app)
entry_lastname.pack(pady=5)

lable_age = tk.Label(app, text="Age: ")
lable_age.pack(pady=5)
birthDate = DateEntry(app, width=16, background ="gray", foreground="white", date_pattern="yyyy-mm-dd")
birthDate.pack(pady=5)

button_frame = tk.Frame(app)
button_frame.pack(pady=10)

savebutton = tk.Button(button_frame, width=10, cursor="hand2", text="Save", command=savedata)
savebutton.pack(side=tk.LEFT, padx=5)

showDataButton = tk.Button(button_frame, width=10, cursor="hand2", text="Show Data", command=showData)
showDataButton.pack(side=tk.LEFT, padx=5)

cancelbutton = tk.Button(button_frame, width=10, cursor="hand2", text="Cancel", command=cancel)
cancelbutton.pack(side=tk.LEFT, padx=5)

app.mainloop()