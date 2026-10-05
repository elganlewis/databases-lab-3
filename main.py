import sqlite3


def update_death(connection: sqlite3.Connection, pet_name: str, date: str) -> None:
    connection.execute(f"UPDATE pet SET death=? WHERE name=?", (date, pet_name))
    if connection.total_changes == 1:
        print(f"updated death = {date} for {pet_name}")
    else:
        print(f"failed to update death for {pet_name}")

def print_details(connection: sqlite3.Connection):
    cursor = connection.execute("SELECT name,owner,species,sex,checkups,birth,death from pet")
    
    for row in cursor:
        print("name:\t\t", row[0])
        print("owner:\t\t", row[1])
        print("species:\t", row[2])
        print("sex:\t\t", row[3])
        print("checkups:\t", row[4])
        print("birth:\t\t", row[5])
        print("death:\t\t", row[6], "\n")

if __name__ == "__main__":
    conn = sqlite3.connect("store.db")
    try:
        with conn:
            print_details(conn)
            update_death(conn, "jeff", "2015-05-13")
            print_details(conn)
    finally:
        conn.close()
