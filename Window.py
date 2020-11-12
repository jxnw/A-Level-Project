import datetime
import random
import smtplib
import sqlite3
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import ImageTk, Image
from string import Template
from validate_email import validate_email

import User
import Booking

# global variables
today = datetime.datetime.now()
IMAGE_MAP = "D:\Program_Files\PyCharmProjects\MusicRoomBookingSystem\map.jpg"
IMAGE_PERIOD = "D:\Program_Files\PyCharmProjects\MusicRoomBookingSystem\period.png"


class Window:
    def __init__(self, master):
        self.master = master
        self.master.resizable(False, False)
        self.title = master.title('Music Room Booking System')
        self.geometry = master.geometry("+500+250")
        self.user = None

        self.frame_content = tk.Frame(self.master)
        self.frame_content.grid(row=0, padx=20, pady=5)
        self.frame_button = tk.Frame(self.master)
        self.frame_button.grid(row=1, padx=20, pady=5)

    def close_window(self):
        self.master.destroy()

    def hide_window(self):
        self.master.withdraw()

    def show_window(self):
        self.master.deiconify()

    def create_button(self, text, row_num, col_num, x=5, y=10, button_width=10, button_height=1, cmd=None, frame=None):
        if frame is None:
            frame = self.frame_button
        button = tk.Button(frame, text=text, command=cmd)
        button.configure(height=button_height, width=button_width)
        button.grid(row=row_num, column=col_num, padx=x, pady=y)


class Login(Window):
    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Login')
        self.user = None

        tk.Label(self.frame_content, text='Music Room\n Booking System', font=('Times New Roman', 20)) \
            .grid(row=0, columnspan=2, padx=5, pady=10)
        tk.Label(self.frame_content, text='E-mail: ').grid(row=1, column=0, padx=5, pady=5)
        tk.Label(self.frame_content, text='Password: ').grid(row=2, column=0, padx=5, pady=5)

        self.entry_email = tk.Entry(self.frame_content, width=25)
        self.entry_email.grid(row=1, column=1, padx=10, pady=5)
        self.entry_email.focus_set()

        self.entry_password = tk.Entry(self.frame_content, width=25, show='*')
        self.entry_password.grid(row=2, column=1, padx=10, pady=5)

        self.create_button('Register', 0, 0, cmd=self.register)
        self.create_button('Submit', 0, 1, cmd=self.submit)

        self.master.mainloop()

    def clear(self):
        """Clear all entry fields"""
        self.entry_email.delete(0, tk.END)
        self.entry_password.delete(0, tk.END)
        self.user = None

    def register(self):
        new_window = tk.Toplevel(self.master)
        Register(new_window)
        new_window.grab_set()

    def submit(self):
        email = self.entry_email.get().lower()
        password = self.entry_password.get()
        try:
            user = User.User()
            if len(email) != 0 and len(password) != 0 and user.try_login(email, password):
                self.user = user
                if self.user.user_id == 0:
                    new_window = tk.Toplevel(self.master)
                    MenuStaff(new_window, self.user)
                else:
                    new_window = tk.Toplevel(self.master)
                    MenuStudent(new_window, self.user)
                self.hide_window()
                self.clear()
            else:
                tk.messagebox.showerror('Error', 'Login details incorrect!')
        except TypeError:
            tk.messagebox.showerror('Error', 'E-mail does not exist!')


class Register(Window):
    """Class for Registration form"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Register')

        tk.Label(self.frame_content, text='Create a New Account', font=('Times New Roman', 20)) \
            .grid(row=0, padx=10, pady=10, columnspan=2)
        tk.Label(self.frame_content, text='Surname: ').grid(row=1, column=0, padx=10, pady=5)
        tk.Label(self.frame_content, text='Name: ').grid(row=2, column=0, padx=10, pady=5)
        tk.Label(self.frame_content, text='Form Group: ').grid(row=3, column=0, padx=10, pady=5)
        tk.Label(self.frame_content, text='E-mail: ').grid(row=4, column=0, padx=10, pady=5)
        tk.Label(self.frame_content, text='Password: ').grid(row=5, column=0, padx=10, pady=5)
        tk.Label(self.frame_content, text='Confirm Password: ').grid(row=6, column=0, padx=10, pady=5)

        self.entry_surname = tk.Entry(self.frame_content, width=25)
        self.entry_surname.grid(row=1, column=1, padx=10, pady=5)
        self.entry_surname.focus_set()

        self.entry_name = tk.Entry(self.frame_content, width=25)
        self.entry_name.grid(row=2, column=1, padx=10, pady=5)

        self.entry_form = tk.Entry(self.frame_content, width=25)
        self.entry_form.grid(row=3, column=1, padx=10, pady=5)

        self.entry_email = tk.Entry(self.frame_content, width=25)
        self.entry_email.grid(row=4, column=1, padx=10, pady=5)

        self.entry_password = tk.Entry(self.frame_content, width=25, show='*')
        self.entry_password.grid(row=5, column=1, padx=10, pady=5)

        self.entry_confirm = tk.Entry(self.frame_content, width=25, show='*')
        self.entry_confirm.grid(row=6, column=1, padx=10, pady=5)

        self.create_button('Cancel', 0, 0, cmd=self.close_window)
        self.create_button('Submit', 0, 1, cmd=self.submit)

    def submit(self):
        """Validate user input"""
        surname = self.entry_surname.get().lower()
        name = self.entry_name.get().lower()
        form = self.entry_form.get().upper()
        email = self.entry_email.get().lower()
        password = self.entry_password.get()
        confirm = self.entry_confirm.get()

        if 0 < len(surname) <= 16:
            if 0 < len(name) <= 16:
                if len(form) == 4:
                    if validate_email(email):
                        if 4 <= len(password) <= 16:
                            if password == confirm:
                                new_user = User.User()
                                if new_user.add_user(surname, name, form, email, password):
                                    tk.messagebox.showerror('Error', 'This email address has been registered')
                                else:
                                    send_email(email, name=name, welcome=True, user_id=new_user.user_id)
                                    tk.messagebox.showinfo('Success', 'Registered successfully! \n'
                                                                      'An email has been sent to your email address.')
                                    self.close_window()
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


class MenuStudent(Window):
    def __init__(self, master, user):
        Window.__init__(self, master)
        self.title = master.title('Menu')
        self.user = user

        text = 'Welcome, ' + self.user.name.capitalize() + '\n(User ID: ' + str(self.user.user_id) + ')'
        tk.Label(self.frame_content, text=text, font=('Times New Roman', 20)).grid(row=0, padx=140, pady=5)

        self.create_button('Make a booking', 0, 0, cmd=self.reserve, button_width=15)
        self.create_button('View my bookings', 1, 0, cmd=self.view, button_width=15)
        self.create_button('Change Password', 2, 0, cmd=self.change_pass, button_width=15)
        self.create_button('Information Page', 3, 0, cmd=self.info_page, button_width=15)
        self.create_button('Logout', 4, 0, cmd=self.logout, button_width=15)

    def reserve(self):
        """Function to show Availability Display"""
        new_window = tk.Toplevel(self.master)
        AvailDisplay(new_window, self.user)
        new_window.grab_set()

    def view(self, user=None):
        """Function to show Booking Viewer"""
        if user is None:
            user = self.user
        new_window = tk.Toplevel(self.master)
        BookingViewer(new_window, user)
        new_window.grab_set()

    def change_pass(self):
        """Function to show Password Changer"""
        new_window = tk.Toplevel(self.master)
        PasswordChanger(new_window, self.user)
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

    def __init__(self, master, user):
        self.user = user
        Window.__init__(self, master)
        self.title = master.title('Menu')

        tk.Label(self.frame_content, text="Staff Menu", font=('Times New Roman', 20)).grid(row=0, padx=140, pady=5)

        self.create_button('Arrange lessons', 0, 0, cmd=self.arrange, button_width=15)
        self.create_button('Manage bookings', 1, 0, cmd=self.manage, button_width=15)
        self.create_button('View user statistics', 2, 0, cmd=self.stats, button_width=15)
        self.create_button('Change Password', 3, 0, cmd=self.change_pass, button_width=15)
        self.create_button('Logout', 4, 0, cmd=self.logout, button_width=15)

    def arrange(self):
        """Method to show Lesson Arranger"""
        new_window = tk.Toplevel(self.master)
        Arranger(new_window, self.user)
        new_window.grab_set()

    def manage(self):
        """Method to show Booking Manager"""
        new_window = tk.Toplevel(self.master)
        Manager(new_window, self.user)
        new_window.grab_set()

    def stats(self):
        """Method to show User Statistics Page"""
        new_window = tk.Toplevel(self.master)
        UserStats(new_window, self.user)
        new_window.grab_set()

    def change_pass(self):
        """Method to show Password Changer"""
        new_window = tk.Toplevel(self.master)
        PasswordChanger(new_window, self.user)
        new_window.grab_set()

    def logout(self):
        """Method to hide the menu window and display the Login Window"""
        self.close_window()
        root.deiconify()


class AvailDisplay(Window):
    def __init__(self, master, user):
        Window.__init__(self, master)
        self.user = user
        self.title = master.title('Make a booking')

        tk.Label(self.frame_content, text='Make a booking', font=('Times New Roman', 20)).grid(row=0, columnspan=9)
        tk.Label(self.frame_content, text='Date: ').grid(row=1, column=2, columnspan=2, padx=5, pady=5)
        tk.Label(self.frame_content, text='Period').grid(row=2, column=0, padx=5, pady=5)

        # label the head row
        for i in range(1, 9):
            room = 'Room' + str(i)
            tk.Label(self.frame_content, text=room).grid(row=2, column=i, padx=10, pady=5)

        # label the first column
        for j in range(1, 11):
            period = str(j)
            tk.Label(self.frame_content, text=period).grid(row=j + 2, column=0, padx=10, pady=5)

        tk.Label(self.frame_content, text='Room: ').grid(row=13, column=2, padx=5, pady=5)
        tk.Label(self.frame_content, text='Period: ').grid(row=13, column=5, padx=5, pady=5)

        # place selection boxes
        current_date = datetime.date.today()
        this_week = []
        for d in range(7):
            day = current_date + datetime.timedelta(days=d)
            this_week.append(str(day))

        self.cmb_date = tk.ttk.Combobox(self.frame_content, text='select a date', state='readonly')
        self.cmb_date.grid(row=1, columnspan=9, padx=5, pady=5)
        self.cmb_date.config(values=this_week)
        self.cmb_date.set(str(current_date))
        self.cmb_date.bind("<<ComboboxSelected>>", self.update)

        self.cmb_room = tk.ttk.Combobox(self.frame_content, text='select a room', state='readonly', width=5)
        self.cmb_room.grid(row=13, column=3, padx=5, pady=5)
        self.cmb_room.config(values=('1', '2', '3', '4', '5', '6', '7', '8'))
        self.cmb_room.set('1')

        self.cmb_period = tk.ttk.Combobox(self.frame_content, text='select a period', state='readonly', width=5)
        self.cmb_period.grid(row=13, column=6, padx=5, pady=5)
        self.cmb_period.config(values=('1', '2', '3', '4', '5', '6', '7', '8', '9', '10'))
        self.cmb_period.set('1')

        self.create_button('Back', 1, 0, cmd=self.close_window, button_width=7)
        self.create_button('Submit', 1, 2, cmd=self.submit, button_width=7)

        self.get_table(str(current_date))

    def update(self, event):
        date = self.cmb_date.get()
        self.get_table(date)

    def get_table(self, t_date):
        """If taken by a student, label name; if taken by a teacher, label 'Lesson'."""
        date = datetime.datetime.strptime(t_date, '%Y-%m-%d')
        week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_name = week[date.weekday()]
        tk.Label(self.frame_content, text=weekday_name, bg='White', width=8).grid(row=1, column=6, padx=5, pady=5)
        for p in range(1, 11):
            for r in range(1, 9):
                record = Booking.Booking(r, t_date, p)
                if record.user_id is None:
                    tk.Label(self.frame_content, text='Available', bg='light green', width=8).grid(row=p + 2, column=r)
                else:
                    if record.user_id == 0:
                        tk.Label(self.frame_content, text='Lesson', bg='red', width=8).grid(row=p + 2, column=r)
                    else:
                        user = User.User(record.user_id)
                        name = user.name.capitalize()
                        tk.Label(self.frame_content, text=name, bg='yellow', width=8).grid(row=p + 2, column=r)

    def submit(self):
        """Make a booking if the room is available for the selected date and period"""
        t_date = self.cmb_date.get()
        t_room = self.cmb_room.get()
        t_period = self.cmb_period.get()
        record = Booking.Booking(t_room, t_date, t_period)
        if record.user_id is None:
            record.add_booking(self.user.user_id)
            text = "Record ID: %d \n Date: %s \n Room ID: %s \n Period: %s" % (record.rec_id, t_date, t_room, t_period)
            tk.messagebox.showinfo('Success', text)

            # send a confirmation email
            send_email(self.user.email, self.user.name, confirm=True, rec_id=record.rec_id,
                       room_id=t_room, t_date=record.date, period=t_period)

            self.user.update()
            self.get_table(self.cmb_date.get())
        else:
            tk.messagebox.showerror('Error', 'The selected room is not available!')


class BookingViewer(Window):
    """Class for Booking Viewer"""

    def __init__(self, master, user):
        Window.__init__(self, master)
        self.user = user
        self.title = master.title('Booking Viewer')

        self.frame_heading = tk.Frame(self.master)
        self.frame_heading.grid(row=0, column=0, padx=30, pady=5)
        self.frame_number = tk.Frame(self.master)
        self.frame_number.grid(row=1, column=0)
        self.frame_table = tk.Frame(self.master)
        self.frame_table.grid(row=2, column=0, columnspan=4)
        self.frame_button = tk.Frame(self.master)
        self.frame_button.grid(row=3, column=0, columnspan=3)

        self.label_title = tk.Label(self.frame_heading, text='Booking Viewer', font=('Times New Roman', 20))
        self.label_title.grid(row=0, column=0, padx=200, pady=15)
        self.label_num = tk.Label(self.frame_number, text='The number of bookings you have made: ' + str(self.user.num))
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

        self.create_button('Previous', 0, 0, cmd=lambda: self.previous(self.start), button_width=7)
        self.create_button('Next', 0, 2, cmd=lambda: self.next(self.start), button_width=7)
        self.create_button('Back', 1, 1, cmd=self.close_window)

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
                taken_booking = Booking.Booking(room_id, date, period, user_id=self.user.user_id)
                taken_booking.cancel()
                self.user.update()
                tk.messagebox.showinfo('Cancellation', 'This booking has been cancelled. ')
                self.close_window()
                MenuStudent.view(self.master, self.user)
        else:
            tk.messagebox.showerror('Error', 'You cannot cancel a booking in the past!')

    def get_booking(self):
        """Select booking records with current user ID"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            t = (self.user.user_id,)
            sql = 'SELECT recID, date, period, roomID FROM tblBookings WHERE userID=? ORDER BY recID DESC'
            result = cursor.execute(sql, t)
            for row in result:
                self.rec_id.append(row[0])
                self.date.append(row[1])
                self.period.append(row[2])
                self.room.append(row[3])

    def label_record(self, start, i):  # 'start' is the index of the first record; 'i' is the row number
        tk.Label(self.frame_table, text='Date').grid(row=0, column=0, padx=50, pady=5)
        tk.Label(self.frame_table, text='Period').grid(row=0, column=1, padx=50, pady=5)
        tk.Label(self.frame_table, text='Room ID').grid(row=0, column=2, padx=50, pady=5)
        tk.Label(self.frame_table, text='Action').grid(row=0, column=3, padx=50, pady=5)
        tk.Label(self.frame_table, text=self.date[start + i]).grid(row=i + 1, column=0, padx=10, pady=1)
        tk.Label(self.frame_table, text=self.period[start + i]).grid(row=i + 1, column=1, padx=10, pady=1)
        tk.Label(self.frame_table, text=self.room[start + i]).grid(row=i + 1, column=2, padx=10, pady=1)

        self.create_button('Cancel', i + 1, 3, cmd=partial(self.click, start + i),
                           button_width=7, button_height=1, frame=self.frame_table)

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

    def __init__(self, master, user):
        Window.__init__(self, master)
        self.user = user
        self.title = master.title('Password Changer')

        tk.Label(self.frame_content, text='Change your password', font=('Times New Roman', 20)).grid(row=0,
                                                                                                     columnspan=2,
                                                                                                     padx=5, pady=5)
        tk.Label(self.frame_content, text='Old Password').grid(row=1, column=0, padx=5, pady=5)
        tk.Label(self.frame_content, text='New Password').grid(row=2, column=0, padx=5, pady=5)
        tk.Label(self.frame_content, text='Confirm New Password').grid(row=3, column=0, padx=5, pady=5)

        self.entry_email = tk.Entry(self.frame_content)
        self.entry_email.grid(row=1, column=1, padx=10, pady=5)
        self.entry_email.focus_set()

        self.old = tk.Entry(self.frame_content, show='*')
        self.old.grid(row=1, column=1, padx=5, pady=5)
        self.old.focus_set()
        self.new = tk.Entry(self.frame_content, show='*')
        self.new.grid(row=2, column=1, padx=5, pady=5)
        self.confirm = tk.Entry(self.frame_content, show='*')
        self.confirm.grid(row=3, column=1, padx=5, pady=5)

        self.create_button('Cancel', 0, 0, button_width=7, cmd=self.close_window)
        self.create_button('Submit', 0, 1, button_width=7, cmd=self.submit)

    def submit(self):
        """Validate user inputs"""
        entry_old = self.old.get()
        entry_new = self.new.get()
        entry_confirm = self.confirm.get()
        if self.user.try_login(self.user.email, entry_old):
            if 4 <= len(entry_new) <= 16:
                if entry_new == entry_confirm:
                    self.user.change_pass(self.confirm.get())
                    tk.messagebox.showinfo('Success', 'Your password has been changed.')
                    self.close_window()
                else:
                    tk.messagebox.showerror('Error', 'Confirmation and password must match')
            else:
                tk.messagebox.showerror('Error', 'Length of password must be 4-16 characters')
        else:
            tk.messagebox.showerror('Error', 'Incorrect original password')


class InfoPage(Window):
    """Class for Information Page"""

    def __init__(self, master):
        Window.__init__(self, master)
        self.title = master.title('Information Page')

        tk.Label(self.frame_content, text='Information Page', font=('Times New Roman', 20)).grid(row=0, columnspan=2)

        # draw the period illustration
        img1 = ImageTk.PhotoImage(Image.open(IMAGE_PERIOD))
        label1 = tk.Label(self.frame_content, image=img1)
        label1.img = img1
        label1.grid(row=1, column=0, padx=5, pady=5)

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
        canvas = FigureCanvasTkAgg(f, master=self.frame_content)
        canvas.draw()
        canvas.get_tk_widget().grid(row=1, column=1, padx=5, pady=5)

        # draw the map
        img2 = ImageTk.PhotoImage(Image.open(IMAGE_MAP))
        label2 = tk.Label(self.frame_content, image=img2)
        label2.img = img2
        label2.grid(row=2, columnspan=2)

        button = tk.Button(self.frame_button, text='Back', width=7, command=self.close_window)
        button.grid(row=0, padx=5, pady=5)


class Arranger(Window):
    """Class for Lesson Arranger"""

    # TODO: Edit this arranger -> Input: available time, numOfStudents, numOfLessons

    def __init__(self, master, user):
        Window.__init__(self, master)
        self.user = user
        self.title = master.title('Lesson Arrangement')

        tk.Label(self.frame_content, text='Lesson Arrangement', font=('Times New Roman', 20)).grid(row=0, columnspan=4)

        tk.Label(self.frame_content, text='Teacher: ').grid(row=1, column=0, padx=5, pady=5)
        tk.Label(self.frame_content, text='Day: ').grid(row=2, column=0, padx=5, pady=5)
        tk.Label(self.frame_content, text='Recurrence: ').grid(row=3, column=0, padx=5, pady=5)
        tk.Label(self.frame_content, text='Instrument Needed: ').grid(row=4, column=0, padx=5, pady=5)
        tk.Label(self.frame_content, text='Number of lessons (per day): ').grid(row=5, column=0, padx=5, pady=5)

        self.cmb_teacher = tk.ttk.Combobox(self.frame_content, state='readonly')
        self.cmb_teacher.grid(row=1, column=1, columnspan=3)
        self.cmb_teacher.config(values=('Anderson', 'Darnell', 'Fletcher', 'Hamilton', 'Huxley',
                                        'Lace', 'Martin', 'Rudland-Simpson', 'Pearson', 'Sage'))
        self.cmb_teacher.set('Anderson')

        self.cmb_day = tk.ttk.Combobox(self.frame_content, state='readonly')
        self.cmb_day.grid(row=2, column=1, columnspan=3)
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
            self.rdb_repeat = tk.Radiobutton(self.frame_content, text=pattern, variable=self.btn_repeat, value=choice,
                                             command=self.get_repeat)
            self.rdb_repeat.grid(row=3, column=int(choice) + 1, padx=20)
        for pattern, choice in instrument:
            self.rdb_instrument = tk.Radiobutton(self.frame_content, text=pattern, variable=self.btn_instrument,
                                                 value=choice,
                                                 command=self.get_instrument)
            self.rdb_instrument.grid(row=4, column=int(choice) + 1, padx=20)

        self.spn_num = tk.Spinbox(self.frame_content, from_=1, to=10, state='readonly')
        self.spn_num.grid(row=5, column=1, columnspan=3)

        self.create_button('Cancel', 0, 0, cmd=self.close_window)
        self.create_button('Ok', 0, 1, cmd=self.submit)

    def get_repeat(self):
        self.repeat = self.btn_repeat.get()

    def get_instrument(self):
        self.instrument = self.btn_instrument.get()

    def submit(self):
        teacher = self.cmb_teacher.get()
        weekday = self.cmb_day.current()
        num = self.spn_num.get()
        new_window = tk.Toplevel(self.master)
        Report(new_window, teacher, weekday, self.repeat, self.instrument, num)
        new_window.grab_set()


class Manager(BookingViewer):
    """Booking Manager for staff"""

    def __init__(self, master, user):
        BookingViewer.__init__(self, master, user)
        self.user = user
        self.title = master.title("Booking Manager")

        self.label_title.grid_forget()
        self.label_num.grid_forget()

        tk.Label(self.frame_content, text='Booking Manager', font=('Times New Roman', 20)).grid(row=0, padx=5, pady=5)

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
                taken_booking = Booking.Booking(room_id, t_date, period, user_id=self.user.user_id)
                taken_booking.cancel()
                self.user.update()

                tk.messagebox.showinfo('Cancellation', 'This booking has been cancelled. ')
                MenuStaff.manage(self.master)
                self.close_window()
        else:
            tk.messagebox.showerror('Error', 'You cannot cancel a booking in the past!')


class Report(Window):
    """Class for Auto-generated Report for Lesson Arrangement"""

    # TODO: Change with Arranger

    def __init__(self, master, teacher, weekday, repeat, instrument, num):
        Window.__init__(self, master)
        self.title = master.title('Auto-generated Report')

        self.teacher = str(teacher)
        self.weekday = int(weekday)
        self.repeat = int(repeat)
        self.instrument = int(instrument)
        self.num = int(num)

        frame_heading = tk.Frame(self.master)
        frame_heading.grid(row=0, padx=30, pady=5)
        frame_number = tk.Frame(self.master)
        frame_number.grid(row=1)
        frame_table = tk.Frame(self.master)
        frame_table.grid(row=2, columnspan=4)

        tk.Label(frame_heading, text='Auto-generated Report', font=('Times New Roman', 20)) \
            .grid(row=0, padx=150, pady=10)
        text = 'Teacher Name: ' + self.teacher
        tk.Label(frame_number, text).grid(row=0, padx=10, pady=5)

        # label the head row
        tk.Label(frame_table, text='Day').grid(row=0, column=0, padx=50, pady=5)
        tk.Label(frame_table, text='Date').grid(row=0, column=1, padx=50, pady=5)
        tk.Label(frame_table, text='Period').grid(row=0, column=2, padx=50, pady=5)
        tk.Label(frame_table, text='Room ID').grid(row=0, column=3, padx=50, pady=5)

        self.date = []
        self.period = []
        self.room = []
        self.wait_list = []
        week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        weekday_name = week[weekday]
        self.display_record(self.weekday)

        for i in range(len(self.room)):
            tk.Label(frame_table, text=weekday_name).grid(row=i + 1, column=0, padx=10, pady=1)
            tk.Label(frame_table, text=self.date[i]).grid(row=i + 1, column=1, padx=10, pady=1)
            tk.Label(frame_table, text=self.period[i]).grid(row=i + 1, column=2, padx=10, pady=1)
            tk.Label(frame_table, text=self.room[i]).grid(row=i + 1, column=3, padx=10, pady=1)

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
            new_booking = Booking.Booking(room, t_date, t_period)
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
                taken_booking = Booking.Booking(self.wait_list[i][0], self.wait_list[i][1], self.wait_list[i][2])
                user = User.User(taken_booking.user_id)
                taken_booking.cancel()
                send_email(email=user.email, name=user.name, cancel=True, rec_id=taken_booking.rec_id,
                           room_id=taken_booking.room_id, t_date=taken_booking.date, period=taken_booking.period,
                           teacher=self.teacher)

        for i in range(len(self.date)):
            new_booking = Booking.Booking(self.room[i], self.date[i], self.period[i])
            new_booking.add_booking(0)  # user ID is 0 for teachers

        tk.messagebox.showinfo('Success', 'Rooms are reserved successfully!')
        self.close_window()


class UserStats(BookingViewer):
    """Class for User Statistics Page"""

    def __init__(self, master, user):
        Window.__init__(self, master)
        self.user = user
        self.title = master.title("User Statistics")

        self.frame_heading = tk.Frame(self.master)
        self.frame_heading.grid(row=0, column=0, padx=30, pady=5)
        self.frame_table = tk.Frame(self.master)
        self.frame_table.grid(row=1, column=0, columnspan=5, pady=5)
        frame_button = tk.Frame(self.master)
        frame_button.grid(row=2, column=0, columnspan=3)

        tk.Label(self.frame_heading, text='User Statistics', font=('Times New Roman', 20)).grid(row=0, column=0,
                                                                                                padx=200, pady=15)

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

        self.create_button('Previous', 0, 0, y=0, cmd=lambda: self.previous(self.start), button_width=7,
                           frame=frame_button)
        self.create_button('Next', 0, 2, y=0, cmd=lambda: self.next(self.start), button_width=7, frame=frame_button)
        self.create_button('Back', 1, 1, cmd=self.close_window, button_width=7, frame=frame_button)

    def label_record(self, start, i):  # 'start' is the index of the first record; 'i' is the row number
        """Display the table of user statistics"""
        tk.Label(self.frame_table, text='User ID').grid(row=0, column=0, padx=25, pady=5)
        tk.Label(self.frame_table, text='Name').grid(row=0, column=1, padx=25, pady=5)
        tk.Label(self.frame_table, text='Surname').grid(row=0, column=2, padx=25, pady=5)
        tk.Label(self.frame_table, text='Form Group').grid(row=0, column=3, padx=25, pady=5)
        tk.Label(self.frame_table, text='Bookings made this month').grid(row=0, column=4, padx=25, pady=5)
        tk.Label(self.frame_table, text=self.user_id[start + i]).grid(row=i + 1, column=0, padx=10, pady=1)
        tk.Label(self.frame_table, text=self.name[start + i]).grid(row=i + 1, column=1, padx=10, pady=1)
        tk.Label(self.frame_table, text=self.surname[start + i]).grid(row=i + 1, column=2, padx=10, pady=1)
        tk.Label(self.frame_table, text=self.form[start + i]).grid(row=i + 1, column=3, padx=10, pady=1)
        tk.Label(self.frame_table, text=self.number[start + i]).grid(row=i + 1, column=4, padx=10, pady=1)

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


# Functions
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

        if today.day == 1:
            cursor.execute("DELETE FROM tblBookings WHERE date < date('now')")
            cursor.execute("UPDATE tblUsers SET numBookings=0")
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
    my_password = "..."

    # Break for testing
    if not validate_email(email):
        return

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


# Main
initialise()
root = tk.Tk()
app = Login(root)
