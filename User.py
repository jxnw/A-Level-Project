import sqlite3


class User:
    def __init__(self, user_id=None):
        """Initialising the user"""
        self.user_id = user_id
        if user_id is None:
            # User does not exist in record
            self.surname = None
            self.name = None
            self.form = None
            self.email = None
            self.num = None
        else:
            with sqlite3.connect('system.db') as conn:
                cursor = conn.cursor()
                sql = "SELECT surname, name, form, email, numBookings FROM tblUsers WHERE userID=?"
                cursor.execute(sql, (user_id,))
                row = cursor.fetchone()
                self.user_id = user_id
                self.surname = row[0]
                self.name = row[1]
                self.form = row[2]
                self.email = row[3]
                self.num = row[4]

    def add_user(self, surname, name, form, email, password):
        """Add a user to tblUsers if the given email does not exist;
            Update user ID"""
        exist = False
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()

            sql_exist = "SELECT EXISTS (SELECT * FROM tblUsers WHERE email=?"
            t = (email,)
            for row in cursor.execute(sql_exist, t):
                if row[0] == 1:
                    exist = True

            if not exist:
                record = [surname, name, form, email, password]
                sql = "INSERT OR IGNORE INTO tblUsers (surname, name, form, email, password) values (?,?,?,?,?)"
                cursor.execute(sql, record)
                conn.commit()
                for result in cursor.execute('SELECT last_insert_rowid()'):
                    self.user_id = result[0]
            return exist

    def try_login(self, email, password):
        """Check if the login details are correct"""
        # TODO: one user may have multiple email addresses?
        valid = False
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = "SELECT password, userID, surname, name, form, numBookings FROM tblUsers WHERE email=?"
            t = (email,)
            cursor.execute(sql, t)
            row = cursor.fetchone()
            if row[0] == password:
                valid = True
                self.email = email
                self.user_id = row[1]
                self.surname = row[2]
                self.name = row[3]
                self.form = row[4]
                self.num = row[5]
        return valid

    def update(self):
        """Update the info of the user object"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = "SELECT surname, name, form, email, numBookings FROM tblUsers WHERE userID=?"
            t = (self.user_id,)
            cursor.execute(sql, t)
            row = cursor.fetchone()
            self.surname = row[0]
            self.name = row[1]
            self.form = row[2]
            self.email = row[3]
            self.num = row[4]

    def change_pass(self, new):
        """Change user's password"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = 'UPDATE tblUsers SET password=? WHERE userID=' + str(self.user_id)
            t = (new,)
            cursor.execute(sql, t)
