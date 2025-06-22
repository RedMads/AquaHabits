import sqlite3, os, time


class HandleDB:

    def __init__(self, db_path:str) -> None:

        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection

        self.cursor.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, user_id TEXT,goal_ml TEXT, join_at TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS user_record(id INTEGER PRIMARY KEY, user_id TEXT, drink_ml TEXT, drink_time TEXT)")

        self.connection.commit()


    def selectDataFromUser(self, user_id:str, target:str) -> str:

        query = self.cursor.execute(f"SELECT {target} FROM users WHERE user_id = ?", (user_id,))
        self.connection.commit()

        return query.fetchone()[0]
    
    def updateGoal(self, user_id:str, new_goal:int) -> None:
        
        self.cursor.execute(f"UPDATE users SET goal_ml = ? WHERE user_id = ? ", (str(new_goal), user_id,))
        self.connection.commit()

    
    def userDrinkWater(self, user_id:str, drink_ml:str) -> None:

        current_time = str(int(time.time()))

        self.cursor.execute(f"INSERT INTO user_record(user_id, drink_ml, drink_time) values (?,?,?)", (user_id, drink_ml, current_time))
        self.connection.commit()


    def getUserDrinkHistory(self, user_id:str) -> list:

        drink_history = self.cursor.execute(f"SELECT drink_ml, drink_time FROM user_record WHERE user_id = ? ORDER BY drink_time ASC", (user_id,))
        return drink_history.fetchall()

    def isUserSignedIn(self, user_id:str) -> bool:

        query = self.cursor.execute("SELECT 1 FROM users WHERE user_id = ? LIMIT 1", (user_id,))
        
        if "None" in str(type(query.fetchone())):
            return False # user does not exist !
        
        else: return True

    def addUser(self, user_id:str, goal_ml:int) -> str:

        join_time = int(time.time())
        self.cursor.execute("INSERT INTO users(user_id, goal_ml, join_at) VALUES (?, ?, ?)", (user_id, str(goal_ml), str(join_time),))
        self.connection.commit()

        user_table_id = self.cursor.execute("SELECT id FROM users WHERE user_id=?", (user_id,))

        return user_table_id.fetchone()[0]


if __name__ == "__main__":

    # test commands
    
    db = HandleDB("database.db")