import sqlite3, os, time


class HandleDB:

    def __init__(self, db_path:str) -> None:

        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection

        self.cursor.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, daily_goal_ml TEXT, joined_at TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS hydration_logs(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, amount_ml TEXT, logged_at TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS daily_goal_achievements(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, achieved_at TEXT)")

        self.connection.commit()


    def selectDataFromUser(self, target:str, table_name:str, user_id:str) -> str:

        query = self.cursor.execute(f"SELECT {target} FROM {table_name} WHERE user_id = ?", (user_id,))
        self.connection.commit()

        return query.fetchone()[0]
    
    def updateGoal(self, user_id:str, new_goal:int) -> None:
        
        self.cursor.execute(f"UPDATE users SET daily_goal_ml = ? WHERE user_id = ? ", (str(new_goal), user_id,))
        self.connection.commit()

    
    def userDrinkWater(self, user_id:str, amount_ml:str) -> None:

        current_time = str(int(time.time()))

        self.cursor.execute(f"INSERT INTO hydration_logs(user_id, amount_ml, logged_at) values (?,?,?)", (user_id, amount_ml, current_time))
        self.connection.commit()

    def getAllUserIDs(self) -> list:

        query = self.cursor.execute("SELECT user_id FROM users")

        user_ids = []

        for user_id in query.fetchall():
            user_ids.append(user_id[0])


        return user_ids


    def deleteHydrationRecord(self, user_id:str) -> None:
        self.cursor.execute(f"DELETE FROM hydration_logs WHERE user_id = ?", (user_id,))
        self.cursor.execute(f"DELETE FROM daily_goal_achievements WHERE user_id = ?", (user_id,))
        self.connection.commit()


    def getUserDrinkHistory(self, user_id:str) -> list:

        drink_history = self.cursor.execute(f"SELECT amount_ml, logged_at FROM hydration_logs WHERE user_id = ? ORDER BY logged_at ASC", (user_id,))
        return drink_history.fetchall()

    def isUserSignedIn(self, user_id:str) -> bool:

        query = self.cursor.execute("SELECT 1 FROM users WHERE user_id = ? LIMIT 1", (user_id,))
        
        if "None" in str(type(query.fetchone())):
            return False # user does not exist !
        
        else: return True

    def userReachedDailyGoal(self, user_id:str) -> None:

        current_time = str(int(time.time()))

        self.cursor.execute("INSERT INTO daily_goal_achievements(user_id, achieved_at) VALUES (?,?)", (user_id, current_time,))
        self.connection.commit()

    def userAllDailyGoals(self, user_id:str) -> int:

        query = self.cursor.execute("SELECT achieved_at FROM daily_goal_achievements WHERE user_id = ?  ORDER BY achieved_at ASC", (user_id,))
        
        return query.fetchall()


    def addUser(self, user_id:str, daily_goal_ml:int) -> str:

        join_time = int(time.time())
        self.cursor.execute("INSERT INTO users(user_id, daily_goal_ml, joined_at) VALUES (?, ?, ?)", (user_id, str(daily_goal_ml), str(join_time),))
        self.connection.commit()

        user_table_id = self.cursor.execute("SELECT id FROM users WHERE user_id=?", (user_id,))

        return user_table_id.fetchone()[0]


if __name__ == "__main__":

    # test commands
    
    db = HandleDB("database.db")