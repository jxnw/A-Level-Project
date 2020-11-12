import sqlite3


class Booking:
    def __init__(self, room_id, t_date, period, rec_id=None, user_id=None):
        self.room_id = int(room_id)
        self.date = str(t_date)
        self.period = int(period)
        self.rec_id = rec_id
        self.user_id = user_id

        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql = "SELECT recID, userID FROM tblBookings WHERE roomID = %d " \
                  "AND date = '%s' and period = %d" % (self.room_id, self.date, self.period)
            cursor.execute(sql)
            row = cursor.fetchone()
            if row is not None:
                self.rec_id = row[0]
                self.user_id = row[1]

    def add_booking(self, user_id):
        if user_id is not None:
            self.user_id = user_id
        record = [self.user_id, self.room_id, self.date, self.period]
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            sql_booking = "INSERT INTO tblBookings (userID, roomID, date, period) VALUES (?,?,?,?)"
            cursor.execute(sql_booking, record)

            sql_num = "SELECT numBookings FROM tblUsers WHERE userID=?"
            user = (self.user_id,)
            cursor.execute(sql_num, user)
            sql_user = "UPDATE tblUsers SET numBookings=" + str(cursor.fetchone()[0] + 1) + " WHERE userID=?"
            cursor.execute(sql_user, user)

            room = (self.room_id,)
            cursor.execute("SELECT numOfBook FROM tblRooms WHERE roomID=?", room)
            sql_room = "UPDATE tblRooms SET numOfBook=" + str(cursor.fetchone()[0] + 1) + " WHERE roomID=?"
            cursor.execute(sql_room, room)

            conn.commit()
            for result in cursor.execute('SELECT last_insert_rowid()'):
                self.rec_id = result[0]

    def cancel(self):
        """Cancel a booking and update numBookings in tblUsers and numOfBook in tblRooms"""
        with sqlite3.connect('system.db') as conn:
            cursor = conn.cursor()
            if self.rec_id is not None:
                cursor.execute("DELETE FROM tblBookings WHERE recID=" + str(self.rec_id))
                conn.commit()

                sql_num = "SELECT numBookings FROM tblUsers WHERE userID=?"
                user = (self.user_id,)
                cursor.execute(sql_num, user)
                sql_user = "UPDATE tblUsers SET numBookings=" + str(cursor.fetchone()[0] - 1) + " WHERE userID=?"
                cursor.execute(sql_user, user)
                conn.commit()

                room = (self.room_id,)
                cursor.execute("SELECT numOfBook FROM tblRooms WHERE roomID=?", room)
                sql_room = "UPDATE tblRooms SET numOfBook=" + str(cursor.fetchone()[0] - 1) + " WHERE roomID=?"
                cursor.execute(sql_room, room)
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
