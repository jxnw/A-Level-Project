# import libraries
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk
import sqlite3
import datetime
import random
import smtplib
from string import Template
from validate_email import validate_email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from PIL import ImageTk, Image


# functions
def initialise():
    with sqlite3.connect('system.db') as conn:
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tblBookings
        (
        recID INTEGER PRIMARY KEY,
        userID INTEGER,
        roomID INTEGER,
        date TEXT,
        period INTEGER,
        FOREIGN KEY (userID) REFERENCES tblUsers(userID)
        FOREIGN KEY (roomID) REFERENCES tblRooms(roomID)
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tblUsers
        (
        userID INTEGER PRIMARY KEY,
        surname TEXT,
        name TEXT,
        form TEXT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        numBookings INTEGER DEFAULT 0
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tblRooms
        (
        roomID INTEGER PRIMARY KEY,
        numOfBook INTEGER DEFAULT 0,
        piano BOOLEAN,
        drum BOOLEAN
        )
        ''')

        staffs = [0, 'musiclovers.qe@gmail.com', 'music']
        cursor.execute("INSERT OR IGNORE INTO tblUsers(userID, email, password) VALUES (?,?,?)", staffs)

        rooms = [(1, 0, True, False),
                 (2, 0, True, False),
                 (3, 0, True, False),
                 (4, 0, True, False),
                 (5, 0, True, False),
                 (6, 0, True, False),
                 (7, 0, True, True),
                 (8, 0, False, True)]

        cursor.executemany("INSERT OR IGNORE INTO tblRooms(roomID, numOfBook, piano, drum) VALUES (?,?,?,?)", rooms)

        conn.commit()

        global today
        today = datetime.datetime.now()
        if today.day == 1:
            cursor.execute("DELETE FROM tblBookings WHERE date < date('now')")
            conn.commit()
            cursor.execute("UPDATE tblUsers SET numBookings=0")
            conn.commit()
            cursor.execute("UPDATE tblRooms SET numOfBook=0")
            conn.commit()


def get_room_data():
    """Get room statistics to draw a graph"""
    data = []
    with sqlite3.connect('system.db') as conn:
        cursor = conn.cursor()
        sql = 'SELECT numOfBook FROM tblRooms'
        for number in cursor.execute(sql):
            data.append(number[0])
    return data


def read_template(filename):
    """Function to read message template"""
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def send_email(email, name, welcome=False, confirm=False, cancel=False,
               user_id=None, rec_id=None, room_id=None, t_date=None, period=None, teacher=None):
    """Send an email to the given email address;
        If welcome=True, send a welcome email; if confirm=True, send a confirmation email;
        If cancel=True, send a cancellation email."""

    my_address = "musiclovers.qe@gmail.com"
    my_password = "Ilovemusic1124"

    # set up the SMTP server
    server = smtplib.SMTP(host='smtp.gmail.com', port=587)
    server.starttls()
    server.login(my_address, my_password)

    msg = MIMEMultipart()  # create a message
    message = None
    subject = None

    if welcome:
        # add in the actual person name to the message template
        message_template = read_template('welcome.txt')
        message = message_template.substitute(PERSON_NAME=name.title(), USER_ID=user_id)
        subject = 'Welcome to Music Room Booking System'

    if confirm:
        # add in the actual person name to the message template
        message_template = read_template('confirmation.txt')
        message = message_template.substitute(PERSON_NAME=name.title(), REC_ID=rec_id, ROOM_ID=room_id,
                                              DATE=t_date, PERIOD=period)
        subject = 'Your Booking for Music Rooms'

    if cancel:
        message_template = read_template('cancellation.txt')
        message = message_template.substitute(PERSON_NAME=name.title(), REC_ID=rec_id, ROOM_ID=room_id,
                                              DATE=t_date, PERIOD=period, TEACHER=teacher)
        subject = 'Your Booking for Music Rooms is Cancelled'

    msg['From'] = my_address
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))  # add in the message body

    # send the message via the server set up earlier.
    server.send_message(msg)
    del msg

    # Terminate the SMTP session and close the connection
    server.quit()


# classes
class User:
    def __init__(self):
        """Initialising the user"""
        self.user_id = None
        self.name = None
        self.email = None
        self.num = None

    def add_user(self, surname, name, form, email, password):
        """Add a user to tblUsers if the given email does not exist;
            Update user ID"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            record = [surname, name, form, email, password]
            sql = "INSERT OR IGNORE INTO tblUsers (surname, name, form, email, password) values (?,?,?,?,?)"
            cursor.execute(sql, record)
            conn.commit()
            for result in cursor.execute('SELECT last_insert_rowid()'):
                self.user_id = result[0]

    def check_password(self, email, password):
        """Check if the login details are correct"""
        valid = False
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = "SELECT password, userID, name, numBookings FROM tblUsers WHERE email=?"
            t = (email,)
            cursor.execute(sql, t)
            row = cursor.fetchone()
            if row[0] == password:
                valid = True
                self.user_id = row[1]
                self.name = row[2]
                self.email = email
                self.num = row[3]
        return valid

    def check_exist(self, email):
        """Check if the email exists in tblUsers"""
        exist = False
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            t = (email,)
            cursor.execute("SELECT userID from tblUsers WHERE email=?", t)
            row = cursor.fetchone()
            if row is not None:
                exist = True
        return exist

    def update_num(self, room_id):
        """Update numBookings in tblUsers and numOfBook in tblRooms when adding a booking"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            self.num = self.num + 1
            sql = "UPDATE tblUsers SET numBookings=" + str(self.num) + " WHERE userID=" + str(self.user_id)
            cursor.execute(sql)

            cursor.execute("SELECT numOfBook FROM tblRooms WHERE roomID=" + str(room_id))
            row = cursor.fetchone()
            n = row[0] + 1
            cursor.execute("UPDATE tblRooms SET numOfBook=" + str(n) + " WHERE roomID=" + str(room_id))

    def cancel(self, rec_id, room_id):
        """Cancel a booking and update numBookings in tblUsers and numOfBook in tblRooms"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            if self.user_id != 0:
                self.num = self.num - 1
                sql = "UPDATE tblUsers SET numBookings=" + str(self.num) + " WHERE userID=" + str(self.user_id)
                cursor.execute(sql)

                cursor.execute("SELECT numOfBook FROM tblRooms WHERE roomID=" + str(room_id))
                row = cursor.fetchone()
                n = row[0] - 1
                cursor.execute("UPDATE tblRooms SET numOfBook=" + str(n) + " WHERE roomID=" + str(room_id))
            cursor.execute("DELETE FROM tblBookings WHERE recID=" + str(rec_id))

    def get_info(self, user_id):
        """Get the name, email of user and the number of bookings made by the user"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = "SELECT name, email, numBookings FROM tblUsers WHERE userID=?"
            t = (user_id,)
            cursor.execute(sql, t)
            row = cursor.fetchone()
            self.name = row[0]
            self.email = row[1]
            self.num = row[2]

    def change_pass(self, new):
        """Change user's password"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = 'UPDATE tblUsers SET password=? WHERE userID=' + str(self.user_id)
            t = (new,)
            cursor.execute(sql, t)


class Booking:
    def __init__(self, room_id, t_date, period):
        self.user_id = None
        self.rec_id = None
        self.room_id = int(room_id)
        self.date = str(t_date)
        self.period = int(period)

    def add_booking(self, user_id):
        record = [user_id, self.room_id, self.date, self.period]
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO tblBookings (userID, roomID, date, period) VALUES (?,?,?,?)"
            cursor.execute(sql, record)
            conn.commit()

    def check_avail(self):
        avail = True
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = "SELECT EXISTS (SELECT * FROM tblBookings WHERE roomID = %d " \
                  "AND date = '%s' and period = %d)" % (self.room_id, self.date, self.period)
            for row in cursor.execute(sql):
                if row[0] == 1:
                    avail = False
        return avail

    def get_rec_id(self):
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = "SELECT recID, userID FROM tblBookings WHERE roomID = %d " \
                  "AND date = '%s' and period = %d" % (self.room_id, self.date, self.period)
            cursor.execute(sql)
            row = cursor.fetchone()
            self.rec_id = row[0]
            self.user_id = row[1]


class Window:
    def __init__(self, master):
        self.master = master
        self.master.resizable(False, False)
        self.title = master.title('Music Room Booking System')
        self.geometry = master.geometry("+500+250")

    def close_window(self):
        self.master.destroy()

    def hide_window(self):
        self.master.withdraw()

    def show_window(self):
        self.master.deiconify()

    def create_label(self, frame, text, rownum, colnum, x=None, y=None, font=('Arial', 16)):
        label = tk.Label(frame, text=text, font=font)
        label.grid(row=rownum, column=colnum, padx=x, pady=y)

    def create_entry(self, frame, rownum, colnum, x=None, y=None, entry_width=25, display=None):
        entry = tk.Entry(frame, width=entry_width, show=display)
        entry.grid(row=rownum, column=colnum, padx=x, pady=y)
        return entry

    def create_button(self, frame, text, rownum, colnum, cmd=None, button_width=15, button_height=2):
        button = tk.Button(frame, text=text, command=cmd)
        button.configure(height=button_height, width=button_width)
        button.grid(row=rownum, column=colnum)


class Login(Window):
    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Login')

        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, column=0, columnspan=2, padx=30, pady=5)
        frame_entry = tk.Frame(self.master)
        frame_entry.grid(row=1, column=0, columnspan=2, padx=25, pady=10)

        self.create_label(frame_heading, 'Music Room\n Booking System', 0, 0, x=70, y=5, font=('Times New Roman', 30))
        self.create_label(frame_entry, 'E-mail: ', 0, 0)
        self.create_label(frame_entry, 'Password: ', 1, 0)

        self.entry_email = self.create_entry(frame_entry, 0, 1, 5, 5)
        self.entry_email.focus_set()
        self.entry_password = self.create_entry(frame_entry, 1, 1, 5, 5, display='*')

        self.create_button(self.master, 'Register', 2, 0, cmd=self.register)
        self.create_button(self.master, 'Submit', 2, 1, cmd=self.submit)

        self.master.mainloop()

    def clear(self):
        """Clear all entry fields"""
        self.entry_email.delete(0, tk.END)
        self.entry_password.delete(0, tk.END)

    def register(self):
        new_window = tk.Toplevel(self.master)
        Register(new_window)
        new_window.grab_set()

    def validation(self, email, password):
        email = email.lower()
        user = User()
        if len(email) != 0 and len(password) != 0:
            if user.check_password(email, password):
                global current_user
                current_user = user
                return True
            else:
                return False

    def submit(self):
        new_window = tk.Toplevel(self.master)
        AvailDisplay(new_window)
        # email = self.entry_email.get()
        # password = self.entry_password.get()
        # try:
        #     if self.validation(email, password):
        #         if current_user.user_id == 0:
        #             new_window = tk.Toplevel(self.master)
        #             MenuStaff(new_window)
        #         else:
        #             new_window = tk.Toplevel(self.master)
        #             MenuStudent(new_window)
        #         self.hide_window()
        #         self.clear()
        #     else:
        #         tk.messagebox.showerror('Error', 'Login details incorrect!')
        # except TypeError:
        #     tk.messagebox.showerror('Error', 'E-mail does not exist!')


class Register(Window):
    """Class for Registration form"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Register')

        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, column=0, columnspan=2, padx=30, pady=5)
        frame_entry = tk.Frame(self.master)
        frame_entry.grid(row=1, column=0, columnspan=2, padx=25, pady=10)

        self.create_label(frame_heading, 'Create a New Account', 0, 0, x=70, y=5, font=('Comic Sans MS', 23))
        self.create_label(frame_entry, 'Surname: ', 0, 0)
        self.create_label(frame_entry, 'Name: ', 1, 0)
        self.create_label(frame_entry, 'Form Group: ', 2, 0)
        self.create_label(frame_entry, 'E-mail: ', 3, 0)
        self.create_label(frame_entry, 'Password: ', 4, 0)
        self.create_label(frame_entry, 'Confirm Password: ', 5, 0)

        self.entry_surname = self.create_entry(frame_entry, 0, 1, 5, 5)
        self.entry_surname.focus_set()
        self.entry_name = self.create_entry(frame_entry, 1, 1, 5, 5)
        self.entry_form = self.create_entry(frame_entry, 2, 1, 5, 5)
        self.entry_email = self.create_entry(frame_entry, 3, 1, 5, 5)
        self.entry_password = self.create_entry(frame_entry, 4, 1, 5, 5, display='*')
        self.entry_confirm = self.create_entry(frame_entry, 5, 1, 5, 5, display='*')

        self.create_button(self.master, 'Cancel', 2, 0, cmd=self.close_window)
        self.create_button(self.master, 'Submit', 2, 1, cmd=self.submit)

    def validation(self):
        """Validate user input"""
        self.surname = self.entry_surname.get().lower()
        self.name = self.entry_name.get().lower()
        self.form = self.entry_form.get().upper()
        self.email = self.entry_email.get().lower()
        self.password = self.entry_password.get()
        self.confirm = self.entry_confirm.get()
        valid = False
        if 0 < len(self.surname) <= 16:
            if 0 < len(self.name) <= 16:
                if len(self.form) == 4:
                    if validate_email(self.email):
                        if 4 <= len(self.password) <= 16:
                            if self.password == self.confirm:
                                valid = True
                            else:
                                tk.messagebox.showerror('Error', 'Confirmation and password must match')
                        else:
                            tk.messagebox.showerror('Error', 'Length of password must be 4-16 characters')
                    else:
                        tk.messagebox.showerror('Error', 'Invalid email address')
                else:
                    tk.messagebox.showerror('Error', 'Length of form must be 4 characters')
            else:
                tk.messagebox.showerror('Error', 'Length of name must be 1-16 characters')
        else:
            tk.messagebox.showerror('Error', 'Length of surname must be 1-16 characters')
        return valid

    def submit(self):
        """Call validation; if email is already registered - report error"""
        if self.validation():
            new_user = User()
            if not new_user.check_exist(self.email):
                new_user.add_user(self.surname, self.name, self.form, self.email, self.password)

                # send a welcome email to user, with user ID and the name of user
                send_email(self.email, name=self.name, welcome=True, user_id=new_user.user_id)

                tk.messagebox.showinfo('Success', 'Registered successfully! \n'
                                                  'An email has been sent to your email address.')
                self.close_window()
            else:
                tk.messagebox.showerror('Error', 'Email address is already registered')


class MenuStudent(Window):
    """Class for Menu for Student"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Menu')

        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, column=0, padx=30, pady=5)
        frame_button = tk.Frame(self.master)
        frame_button.grid(row=1, column=0, padx=25, pady=10)

        text = 'Welcome, ' + current_user.name.capitalize() + '\n(User ID: ' + str(current_user.user_id) + ')'

        self.create_label(frame_heading, text, 0, 0, 140, 5, font=('Comic Sans MS', 25))

        self.create_button(frame_button, 'Make a booking', 0, 0, cmd=self.reserve)
        self.create_button(frame_button, 'View my bookings', 1, 0, cmd=self.view)
        self.create_button(frame_button, 'Change Password', 2, 0, cmd=self.change_pass)
        self.create_button(frame_button, 'Information Page', 3, 0, cmd=self.info_page)
        self.create_button(frame_button, 'Logout', 4, 0, cmd=self.logout)

    def reserve(self):
        """Function to show Availability Display"""
        new_window = tk.Toplevel(self.master)
        AvailDisplay(new_window)
        new_window.grab_set()

    def view(self):
        """Function to show Booking Viewer"""
        new_window = tk.Toplevel(self.master)
        BookingViewer(new_window)
        new_window.grab_set()

    def change_pass(self):
        """Function to show Password Changer"""
        new_window = tk.Toplevel(self.master)
        PasswordChanger(new_window)
        new_window.grab_set()

    def info_page(self):
        """Function to show Information Page"""
        new_window = tk.Toplevel(self.master)
        InfoPage(new_window)
        new_window.grab_set()

    def logout(self):
        """Function to hide the menu window and display the Login Window"""
        self.close_window()
        root.deiconify()


class MenuStaff(Window):
    """Class for Menu for Staff"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Menu')

        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, column=0, padx=30, pady=5)
        frame_button = tk.Frame(self.master)
        frame_button.grid(row=1, column=0, padx=25, pady=10)

        self.create_label(frame_heading, "Staff Menu", 0, 0, 140, 5, font=('Comic Sans MS', 25))
        self.create_button(frame_button, 'Arrange lessons', 0, 0, cmd=self.arrange)
        self.create_button(frame_button, 'Manage bookings', 1, 0, cmd=self.manage)
        self.create_button(frame_button, 'View user statistics', 2, 0, cmd=self.stats)

        self.create_button(frame_button, 'Change Password', 3, 0, cmd=self.change_pass)
        self.create_button(frame_button, 'Logout', 4, 0, cmd=self.logout)

    def arrange(self):
        """Method to show Lesson Arranger"""
        new_window = tk.Toplevel(self.master)
        Arranger(new_window)
        new_window.grab_set()

    def manage(self):
        """Method to show Booking Manager"""
        new_window = tk.Toplevel(self.master)
        Manager(new_window)
        new_window.grab_set()

    def stats(self):
        """Method to show User Statistics Page"""
        new_window = tk.Toplevel(self.master)
        UserStats(new_window)
        new_window.grab_set()

    def change_pass(self):
        """Method to show Password Changer"""
        new_window = tk.Toplevel(self.master)
        PasswordChanger(new_window)
        new_window.grab_set()

    def logout(self):
        """Method to hide the menu window and display the Login Window"""
        self.close_window()
        root.deiconify()


class AvailDisplay(Window):
    """Class for Availability Display"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Make a booking')

        # frame
        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, column=0, padx=30, pady=5)
        self.frame_date = tk.Frame(self.master)
        self.frame_date.grid(row=1, column=0, columnspan=3)
        self.frame_table = tk.Frame(self.master)
        self.frame_table.grid(row=2, column=0, padx=30)
        frame_selection = tk.Frame(self.master)
        frame_selection.grid(row=3, column=0, columnspan=4)

        self.create_label(frame_heading, 'Make a booking', 0, 0, 0, 15, font=('Comic Sans MS', 25))
        self.create_label(self.frame_table, 'Period', 0, 0, 10, 5)
        self.create_label(self.frame_date, 'Date: ', 0, 0, 5, 5)
        self.create_label(frame_selection, 'Room: ', 0, 0, 5, 5)
        self.create_label(frame_selection, 'Period: ', 0, 2, 5, 5)

        # label the head row
        for i in range(1, 9):
            room = 'Room' + str(i)
            self.create_label(self.frame_table, room, 0, i, 10, 5)

        # label the first column
        for j in range(1, 11):
            period = str(j)
            self.create_label(self.frame_table, period, j, 0, 10, 5)

        # place selection boxes
        current_date = datetime.date.today()
        this_week = []
        for d in range(7):
            day = current_date + datetime.timedelta(days=d)
            this_week.append(str(day))

        self.cmb_date = tk.ttk.Combobox(self.frame_date, text='select a date', state='readonly')
        self.cmb_date.grid(row=0, column=1, padx=5, pady=5)
        self.cmb_date.config(values=this_week)
        self.cmb_date.set(str(current_date))
        self.cmb_date.bind("<<ComboboxSelected>>", self.update)

        self.cmb_room = tk.ttk.Combobox(frame_selection, text='select a room', state='readonly', width=5)
        self.cmb_room.grid(row=0, column=1, padx=5, pady=5)
        self.cmb_room.config(values=('1', '2', '3', '4', '5', '6', '7', '8'))
        self.cmb_room.set('1')

        self.cmb_period = tk.ttk.Combobox(frame_selection, text='select a period', state='readonly', width=5)
        self.cmb_period.grid(row=0, column=3)
        self.cmb_period.config(values=('1', '2', '3', '4', '5', '6', '7', '8', '9', '10'))
        self.cmb_period.set('1')

        self.create_button(frame_selection, 'Cancel', 1, 0, cmd=self.close_window, button_width=7)
        self.create_button(frame_selection, 'Submit', 1, 2, cmd=self.submit, button_width=7)

        self.get_table(str(current_date))

    def update(self, event):
        date = self.cmb_date.get()
        self.get_table(date)

    def get_table(self, t_date):
        """If taken by a student, label name; if taken by a teacher, label 'Lesson'."""
        date = datetime.datetime.strptime(t_date, '%Y-%m-%d')
        week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_name = week[date.weekday()]
        tk.Label(self.frame_date, text=weekday_name, bg='White', width=8).grid(row=0, column=2)
        for p in range(1, 11):
            for r in range(1, 9):
                record = Booking(r, t_date, p)
                if record.check_avail():
                    tk.Label(self.frame_table, text='Available', bg='light green', width=8).grid(row=p, column=r)
                else:
                    record.get_rec_id()
                    if record.user_id == 0:
                        tk.Label(self.frame_table, text='Lesson', bg='red', width=8).grid(row=p, column=r)
                    else:
                        user = User()
                        user.get_info(record.user_id)
                        name = user.name.capitalize()
                        tk.Label(self.frame_table, text=name, bg='yellow', width=8).grid(row=p, column=r)

    def submit(self):
        """Make a booking if the room is available for the selected date and period"""
        t_date = self.cmb_date.get()
        t_room = self.cmb_room.get()
        t_period = self.cmb_period.get()
        record = Booking(t_room, t_date, t_period)
        if record.check_avail():
            record.add_booking(current_user.user_id)
            record.get_rec_id()
            text = "Record ID: %d \n Date: %s \n Room ID: %s \n Period: %s" % (record.rec_id, t_date, t_room, t_period)
            tk.messagebox.showinfo('Success', text)

            # send a confirmation email
            send_email(current_user.email, current_user.name, confirm=True, rec_id=record.rec_id,
                       room_id=t_room, t_date=record.date, period=t_period)

            current_user.update_num(t_room)
            self.get_table(self.cmb_date.get())
        else:
            tk.messagebox.showerror('Error', 'The selected room is not available!')


class BookingViewer(Window):
    """Class for Booking Viewer"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Booking Viewer')

        self.frame_heading = tk.Frame(self.master)
        self.frame_heading.grid(row=0, column=0, padx=30, pady=5)
        frame_number = tk.Frame(self.master)
        frame_number.grid(row=1, column=0)
        self.frame_table = tk.Frame(self.master)
        self.frame_table.grid(row=2, column=0, columnspan=4)
        frame_button = tk.Frame(self.master)
        frame_button.grid(row=3, column=0, columnspan=3)

        self.label_title = tk.Label(self.frame_heading, text='Booking Viewer', font=('Comic Sans MS', 25))
        self.label_title.grid(row=0, column=0, padx=200, pady=15)
        self.label_num = tk.Label(frame_number, text='The number of bookings you have made: ' + str(current_user.num))
        self.label_num.grid(row=0, column=0, padx=10, pady=10)

        # label the records
        self.rec_id = []
        self.date = []
        self.period = []
        self.room = []
        self.get_booking()

        self.start = 0  # index of the first record
        self.num = len(self.rec_id)  # the number of records to be displayed

        if self.num < 5:  # if the number of records is smaller than 5
            for i in range(len(self.rec_id)):
                self.label_record(self.start, i)
            self.num = self.num - 5  # disable 'next' button by making self.num negative
        else:
            for i in range(5):
                self.label_record(self.start, i)
            self.num = self.num - 5  # 5 of the records have been displayed, the number remaining is (self.num - 5)

        self.create_button(frame_button, 'Previous', 0, 0, cmd=lambda: self.previous(self.start), button_width=7)
        self.create_button(frame_button, 'Next', 0, 2, cmd=lambda: self.next(self.start), button_width=7)
        self.create_button(frame_button, 'Back', 1, 1, cmd=self.close_window)

    def click(self, index):
        """Display confirmation window"""
        rec_id = self.rec_id[index]
        room_id = self.room[index]
        period = self.period[index]
        date = self.date[index]
        t_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        if t_date > today:
            text = "Do you want to cancel this booking? \nRecord ID: %d \n Date: %s \n Room ID: %s \n Period: %s" \
                   % (rec_id, date, room_id, period)
            if tk.messagebox.askyesno('Cancellation', text):
                current_user.cancel(rec_id, room_id)
                tk.messagebox.showinfo('Cancellation', 'This booking has been cancelled. ')
                MenuStudent.view(self.master)
                self.close_window()
        else:
            tk.messagebox.showerror('Error', 'You cannot cancel a booking in the past!')

    def get_booking(self):
        """Select booking records with current user ID"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            t = (current_user.user_id,)
            sql = 'SELECT recID, date, period, roomID FROM tblBookings WHERE userID=? ORDER BY recID DESC'
            result = cursor.execute(sql, t)
            for row in result:
                self.rec_id.append(row[0])
                self.date.append(row[1])
                self.period.append(row[2])
                self.room.append(row[3])

    def label_record(self, start, i):  # 'start' is the index of the first record; 'i' is the row number
        self.create_label(self.frame_table, 'Date', 0, 0, 50, 5)
        self.create_label(self.frame_table, 'Period', 0, 1, 50, 5)
        self.create_label(self.frame_table, 'Room ID', 0, 2, 50, 5)
        self.create_label(self.frame_table, 'Action', 0, 3, 50, 5)
        self.create_label(self.frame_table, self.date[start + i], i + 1, 0, 10, 1)
        self.create_label(self.frame_table, self.period[start + i], i + 1, 1, 10, 1)
        self.create_label(self.frame_table, self.room[start + i], i + 1, 2, 10, 1)
        self.create_button(self.frame_table, 'Cancel', i + 1, 3, cmd=partial(self.click, start + i),
                           button_width=7, button_height=1)

    def next(self, start):  # 'start' is the index of the first record of current page
        """Next Page; maximum 5"""
        if self.num <= 0:  # check if the number of records to be displayed is negative or zero
            tk.messagebox.showerror('Alert', 'This is the last page.')
        else:
            self.destroy_frame()
            self.start = start + 5  # index of the first record of next page = index of first record of current page + 5
            if self.num < 5:  # check if the number of records to be displayed is smaller than 5
                for i in range(self.num):
                    self.label_record(self.start, i)
                self.num = self.num - 5  # disable 'next' button by making self.num negative
            else:
                for i in range(5):
                    self.label_record(self.start, i)
                self.num = self.num - 5  # 5 of the records have been displayed, the number remaining is (self.num - 5)

    def previous(self, start):  # 'start' is the index of the first record of current page
        """Previous Page; maximum 5"""
        if start < 5:  # if the first index is less than 5
            tk.messagebox.showerror('Alert', 'This is the first page.')
        else:
            self.destroy_frame()
            self.start = start - 5  # index of first record of previous page = index of first record of current page - 5
            for i in range(5):  # the 'previous' page can only display 5 records
                self.label_record(self.start, i)
            self.num = self.num + 5  # the number of records 'after' the current page to be displayed is (self.num+5)

    def destroy_frame(self):
        self.frame_table.grid_forget()  # forget frame_table and create a new one
        self.frame_table = tk.Frame(self.master)
        self.frame_table.grid(row=2, column=0, columnspan=4)


class PasswordChanger(Window):
    """Class for Password Changer"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Password Changer')

        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, column=0, columnspan=2, padx=30, pady=5)
        frame_entry = tk.Frame(self.master)
        frame_entry.grid(row=1, column=0, columnspan=2, padx=25, pady=10)

        self.create_label(frame_heading, 'Change your password', 0, 0, 0, 5, font=('Comic Sans MS', 25))
        self.create_label(frame_entry, 'Old Password: ', 0, 0, 10, 10)
        self.create_label(frame_entry, 'New Password: ', 1, 0, 10, 10)
        self.create_label(frame_entry, 'Confirm New Password: ', 2, 0, 10, 10)

        self.old = self.create_entry(frame_entry, 0, 1, 5, 5, display='*')
        self.old.focus_set()
        self.new = self.create_entry(frame_entry, 1, 1, 5, 5, display='*')
        self.confirm = self.create_entry(frame_entry, 2, 1, 5, 5, display='*')

        self.create_button(self.master, 'Cancel', 2, 0, button_width=7, cmd=self.close_window)
        self.create_button(self.master, 'Submit', 2, 1, button_width=7, cmd=self.submit)

    def validation(self):
        """Validate user inputs"""
        entry_old = self.old.get()
        entry_new = self.new.get()
        entry_confirm = self.confirm.get()
        valid = False
        if current_user.check_password(current_user.email, entry_old):
            if 4 <= len(entry_new) <= 16:
                if entry_new == entry_confirm:
                    valid = True
                else:
                    tk.messagebox.showerror('Error', 'Confirmation and password must match')
            else:
                tk.messagebox.showerror('Error', 'Length of password must be 4-16 characters')
        else:
            tk.messagebox.showerror('Error', 'Incorrect original password')
        return valid

    def submit(self):
        """Call method validation; if valid, change the password"""
        if self.validation():
            current_user.change_pass(self.confirm.get())
            tk.messagebox.showinfo('Success', 'Your password has been changed.')
            self.close_window()


class InfoPage(Window):
    """Class for Information Page"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Information Page')

        frame_heading = tk.Frame(self.master)
        frame_heading.pack(side='top', pady=15)
        frame_button = tk.Frame(self.master)
        frame_button.pack(side='bottom', pady=5)
        frame_map = tk.Frame(self.master)
        frame_map.pack(side='bottom')
        frame_period = tk.Frame(self.master)
        frame_period.pack(side='left', padx=5)
        frame_chart = tk.Frame(self.master)
        frame_chart.pack(side='right', padx=5, pady=5)

        tk.Label(frame_heading, text='Information Page', font=('Comic Sans MS', 25)).pack()
        self.create_button(frame_button, 'Back', 0, 0, cmd=self.close_window, button_width=5)

        # draw the period illustration
        img1 = ImageTk.PhotoImage(Image.open("/Users/wangjiaxin/PycharmProjects/ComputingProject/period.png"))
        label1 = tk.Label(frame_period, image=img1)
        label1.img = img1
        label1.pack()

        # draw the bar chart
        f = Figure(figsize=(4, 4), dpi=80)
        ax = f.add_subplot(111)
        names = ['1', '2', '3', '4', '5', '6', '7', '8']  # index of the rooms
        data = get_room_data()  # Call function to get room data
        width = .8
        ax.bar(names, data, width)
        ax.set_title('Popular bookings this month\n', fontdict={'family': 'Arial', 'weight': 'bold', 'size': 14})
        ax.set_xlabel('Room')  # Set the label of x axis
        ax.set_ylabel('Number of bookings')  # Set the label of y axis
        ax.set_ylim(ymin=0)  # Set the minimum value of y axis
        canvas = FigureCanvasTkAgg(f, master=frame_chart)
        canvas.draw()
        canvas.get_tk_widget().pack()

        # draw the map
        img2 = ImageTk.PhotoImage(Image.open("/Users/wangjiaxin/PycharmProjects/ComputingProject/map.jpg"))
        label2 = tk.Label(frame_map, image=img2)
        label2.img = img2
        label2.pack()


class Arranger(Window):
    """Class for Lesson Arranger"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Lesson Arrangement')

        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, column=0, padx=30, pady=5)
        frame_cmb = tk.Frame(self.master)
        frame_cmb.grid(row=1, column=0)
        frame_rdb = tk.Frame(self.master)
        frame_rdb.grid(row=2, column=0)
        frame_spn = tk.Frame(self.master)
        frame_spn.grid(row=3, column=0, columnspan=2)

        self.create_label(frame_heading, 'Lesson Arrangement', 0, 0, 0, 15, font=('Comic Sans MS', 25))
        self.create_label(frame_cmb, 'Teacher: ', 0, 0, 10, 10)
        self.create_label(frame_cmb, 'Day: ', 1, 0, 10, 10)
        self.create_label(frame_rdb, 'Recurrence: ', 0, 0, 10, 10)
        self.create_label(frame_rdb, 'Instrument Needed: ', 1, 0, 10, 10)
        self.create_label(frame_spn, 'Number of lessons(per day): ', 0, 0, 10, 10)

        self.cmb_teacher = tk.ttk.Combobox(frame_cmb, state='readonly', width=15)
        self.cmb_teacher.grid(row=0, column=1)
        self.cmb_teacher.config(values=('Anderson', 'Darnell', 'Fletcher', 'Hamilton', 'Huxley',
                                        'Lace', 'Martin', 'Rudland-Simpson', 'Pearson', 'Sage'))
        self.cmb_teacher.set('Anderson')
        self.cmb_day = tk.ttk.Combobox(frame_cmb, state='readonly', width=15)
        self.cmb_day.grid(row=1, column=1)
        self.cmb_day.config(values=('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'))
        self.cmb_day.set('Monday')

        repeat = [('Weekly', 0), ('No', 1)]
        instrument = [('Piano', 0), ('Drums', 1), ('N/A', 2)]
        self.btn_repeat = tk.StringVar()
        self.btn_repeat.set(0)
        self.btn_instrument = tk.StringVar()
        self.btn_instrument.set(0)
        self.repeat = 0
        self.instrument = 0

        for pattern, choice in repeat:
            self.rdb_repeat = tk.Radiobutton(frame_rdb, text=pattern, variable=self.btn_repeat, value=choice,
                                             command=self.get_repeat)
            self.rdb_repeat.grid(row=0, column=int(choice) + 1, padx=20)
        for pattern, choice in instrument:
            self.rdb_instrument = tk.Radiobutton(frame_rdb, text=pattern, variable=self.btn_instrument, value=choice,
                                                 command=self.get_instrument)
            self.rdb_instrument.grid(row=1, column=int(choice) + 1, padx=20)

        self.spn_num = tk.Spinbox(frame_spn, from_=1, to=10, state='readonly')
        self.spn_num.grid(row=0, column=1)

        self.create_button(frame_spn, 'Cancel', 4, 0, cmd=self.close_window)
        self.create_button(frame_spn, 'Ok', 4, 1, cmd=self.submit)

    def get_repeat(self):
        self.repeat = self.btn_repeat.get()

    def get_instrument(self):
        self.instrument = self.btn_instrument.get()

    def submit(self):
        self.teacher = self.cmb_teacher.get()
        self.weekday = self.cmb_day.current()
        self.num = self.spn_num.get()
        new_window = tk.Toplevel(self.master)
        Report(new_window, self.teacher, self.weekday, self.repeat, self.instrument, self.num)
        new_window.grab_set()


class Manager(BookingViewer):
    """Booking Manager for staff"""

    def __init__(self, master):
        BookingViewer.__init__(self, master)
        self.title = master.title("Booking Manager")

        self.label_title.grid_forget()
        self.label_num.grid_forget()
        self.create_label(self.frame_heading, 'Booking Manager', 0, 0, 200, 15, font=('Comic Sans MS', 25))

    def click(self, index):
        """Display confirmation window"""
        rec_id = self.rec_id[index]
        room_id = self.room[index]
        period = self.period[index]
        date = self.date[index]
        t_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        if t_date > today:
            text = "Do you want to cancel this booking? \nRecord ID: %d \n Date: %s \n Room ID: %s \n Period: %s" \
                   % (rec_id, date, room_id, period)
            if tk.messagebox.askyesno('Cancellation', text):
                current_user.cancel(rec_id, room_id)
                tk.messagebox.showinfo('Cancellation', 'This booking has been cancelled. ')
                MenuStaff.manage(self.master)
                self.close_window()
        else:
            tk.messagebox.showerror('Error', 'You cannot cancel a booking in the past!')


class Report(Window):
    """Class for Auto-generated Report for Lesson Arrangement"""

    def __init__(self, master, teacher, weekday, repeat, instrument, num):
        Window.__init__(self, master)
        self.title = master.title('Auto-generated Report')

        self.teacher = str(teacher)
        self.weekday = int(weekday)
        self.repeat = int(repeat)
        self.instrument = int(instrument)
        self.num = int(num)

        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, column=0, padx=30, pady=5)
        frame_number = tk.Frame(self.master)
        frame_number.grid(row=1, column=0)
        frame_table = tk.Frame(self.master)
        frame_table.grid(row=2, column=0, columnspan=4)

        self.create_label(frame_heading, 'Auto-generated Report', 0, 0, 150, 10, font=('Comic Sans MS', 25))
        text = 'Teacher Name: ' + self.teacher
        self.create_label(frame_number, text, 0, 0, 10, 5)

        # label the head row
        self.create_label(frame_table, 'Day', 0, 0, 50, 5)
        self.create_label(frame_table, 'Date', 0, 1, 50, 5)
        self.create_label(frame_table, 'Period', 0, 2, 50, 5)
        self.create_label(frame_table, 'Room ID', 0, 3, 50, 5)

        self.date = []
        self.period = []
        self.room = []
        self.wait_list = []
        week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        weekday_name = week[weekday]
        self.display_record(self.weekday)

        for i in range(len(self.room)):
            self.create_label(frame_table, weekday_name, i + 1, 0, 10, 1)
            self.create_label(frame_table, self.date[i], i + 1, 1, 10, 1)
            self.create_label(frame_table, self.period[i], i + 1, 2, 10, 1)
            self.create_label(frame_table, self.room[i], i + 1, 3, 10, 1)

        self.create_button(frame_table, 'Back', len(self.room) + 1, 1, cmd=self.close_window)
        self.create_button(frame_table, 'Confirm', len(self.room) + 1, 2, cmd=self.submit)

    def display_record(self, weekday):
        """Method to decide the date for the given weekday"""
        current_weekday = today.weekday()
        delta = weekday - current_weekday
        if delta < 0:
            delta = delta + 7
        t_date = datetime.date.today() + datetime.timedelta(days=delta)

        record_a = self.generate_records(t_date)
        for i in range(len(record_a)):
            self.date.append(record_a[i][1])
            self.period.append(record_a[i][2])
            self.room.append(record_a[i][0])

        if self.repeat == 0:
            t_date = t_date + datetime.timedelta(days=7)
            record_b = self.generate_records(t_date)
            for i in range(len(record_b)):
                self.date.append(record_b[i][1])
                self.period.append(record_b[i][2])
                self.room.append(record_b[i][0])

    def generate_records(self, t_date):
        """Return a list of records for the given date"""
        records = []
        period = 1
        num_left = self.num
        while num_left > 0:
            if period > 10:
                break
            record = self.find_room(t_date, period)
            if len(record) == 0:  # if no rooms are available:
                period = period + 1  # check for next period
            else:
                records.append(record)
                period = period + 1
                num_left = num_left - 1

        if num_left > 0:
            for j in range(num_left):  # this is the number of lessons left to be arranged
                records.append(self.wait_list[j])

        return records

    def find_room(self, t_date, t_period):
        """Function to choose the room for the given date and period"""
        room_id = []
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            if self.instrument == 0:
                sql = "SELECT roomID from tblRooms WHERE piano=1"
            elif self.instrument == 1:
                sql = "SELECT roomID from tblRooms WHERE drum=1"
            else:
                sql = "SELECT roomID from tblRooms"
            for result in cursor.execute(sql):
                room_id.append(result[0])

        random.shuffle(room_id)

        for i in range(len(room_id)):
            room = room_id[i]
            new_booking = Booking(room, t_date, t_period)
            if new_booking.check_avail():
                record = [room, str(t_date), t_period]
                return record

        record = [random.choice(room_id), str(t_date), t_period]
        self.wait_list.append(record)
        return []

    def submit(self):
        """Submit the form; cancel user bookings; send an email to users whose bookings are cancelled"""
        if len(self.wait_list) != 0:
            for i in range(len(self.wait_list)):
                taken_booking = Booking(self.wait_list[i][0], self.wait_list[i][1], self.wait_list[i][2])
                taken_booking.get_rec_id()  # this will get the userID and recID of the booking
                user = User()
                user.user_id = taken_booking.user_id
                user.get_info(user.user_id)  # this will get user.name, user.email, user.num
                user.cancel(taken_booking.rec_id, taken_booking.room_id)
                send_email(email=user.email, name=user.name, cancel=True, rec_id=taken_booking.rec_id,
                           room_id=taken_booking.room_id, t_date=taken_booking.date, period=taken_booking.period,
                           teacher=self.teacher)

        for i in range(len(self.date)):
            new_booking = Booking(self.room[i], self.date[i], self.period[i])
            new_booking.add_booking(0)  # user ID is 0 for teachers

        tk.messagebox.showinfo('Success', 'Rooms are reserved successfully!')
        self.close_window()


class UserStats(BookingViewer):
    """Class for User Statistics Page / inherit booking viewer?"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title("User Statistics")

        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, column=0, padx=30, pady=5)
        self.frame_table = tk.Frame(self.master)
        self.frame_table.grid(row=1, column=0, columnspan=5)
        frame_button = tk.Frame(self.master)
        frame_button.grid(row=2, column=0, columnspan=3)

        self.create_label(frame_heading, 'User Statistics', 0, 0, 200, 15, font=('Comic Sans MS', 25))

        # label the records
        self.user_id = []
        self.name = []
        self.surname = []
        self.form = []
        self.number = []
        self.find_record()

        self.start = 0  # index of the first record
        self.num = len(self.user_id)  # the number of records to be displayed

        if self.num < 5:  # if the number of records is smaller than 5
            for i in range(len(self.user_id)):
                self.label_record(self.start, i)
            self.num = self.num - 5  # disable 'next' button by making self.num negative
        else:
            for i in range(5):
                self.label_record(self.start, i)
            self.num = self.num - 5  # 5 of the records have been displayed, the number remaining is (self.num - 5)

        self.create_button(frame_button, 'Previous', 0, 0, cmd=lambda: self.previous(self.start), button_width=7)
        self.create_button(frame_button, 'Next', 0, 2, cmd=lambda: self.next(self.start), button_width=7)
        self.create_button(frame_button, 'Back', 1, 1, cmd=self.close_window)

    def label_record(self, start, i):  # 'start' is the index of the first record; 'i' is the row number
        """Display the table of user statistics"""
        self.create_label(self.frame_table, 'User ID', 0, 0, 25, 5)
        self.create_label(self.frame_table, 'Name', 0, 1, 25, 5)
        self.create_label(self.frame_table, 'Surname', 0, 2, 25, 5)
        self.create_label(self.frame_table, 'Form Group', 0, 3, 25, 5)
        self.create_label(self.frame_table, 'Bookings made this month', 0, 4, 25, 5)
        self.create_label(self.frame_table, self.user_id[start + i], i + 1, 0, 10, 1)
        self.create_label(self.frame_table, self.name[start + i].capitalize(), i + 1, 1, 10, 1)
        self.create_label(self.frame_table, self.surname[start + i].capitalize(), i + 1, 2, 10, 1)
        self.create_label(self.frame_table, self.form[start + i], i + 1, 3, 10, 1)
        self.create_label(self.frame_table, self.number[start + i], i + 1, 4, 10, 1)

    def find_record(self):
        """Rank all the users except the staff account by numBookings"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = 'SELECT userID, name, surname, form, numBookings FROM tblUsers ORDER BY numBookings DESC'
            result = cursor.execute(sql)
            for row in result:
                if row[0] != 0:
                    self.user_id.append(row[0])
                    self.name.append(row[1])
                    self.surname.append(row[2])
                    self.form.append(row[3])
                    self.number.append(row[4])

    def destroy_frame(self):
        self.frame_table.grid_forget()  # forget frame_table and create a new one
        self.frame_table = tk.Frame(self.master)
        self.frame_table.grid(row=1, column=0, columnspan=5)


# main program
initialise()
root = tk.Tk()
app = Login(root)
