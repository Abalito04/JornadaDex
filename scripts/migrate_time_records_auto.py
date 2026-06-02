import sqlite3
from pathlib import Path


def main():
    db_path = Path("instance/time_control.db")
    if not db_path.exists():
        raise SystemExit("Database not found. Run flask init-db first.")

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    columns = cur.execute("PRAGMA table_info(time_records)").fetchall()
    end_time = next((col for col in columns if col[1] == "end_time"), None)
    hours = next((col for col in columns if col[1] == "hours"), None)
    if end_time and end_time[3] == 0 and hours and hours[4] == "0":
        print("time_records already migrated.")
        con.close()
        return

    cur.execute("PRAGMA foreign_keys=off")
    cur.execute("ALTER TABLE time_records RENAME TO time_records_old")
    cur.execute(
        """
        CREATE TABLE time_records (
            id INTEGER NOT NULL,
            company_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            area_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            record_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME,
            hours NUMERIC(8, 2) NOT NULL DEFAULT 0,
            observations TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            deleted_at DATETIME,
            created_by INTEGER,
            updated_by INTEGER,
            deleted_by INTEGER,
            PRIMARY KEY (id),
            FOREIGN KEY(company_id) REFERENCES companies (id),
            FOREIGN KEY(employee_id) REFERENCES employees (id),
            FOREIGN KEY(area_id) REFERENCES areas (id),
            FOREIGN KEY(task_id) REFERENCES tasks (id),
            FOREIGN KEY(created_by) REFERENCES users (id),
            FOREIGN KEY(updated_by) REFERENCES users (id),
            FOREIGN KEY(deleted_by) REFERENCES users (id)
        )
        """
    )
    cur.execute(
        """
        INSERT INTO time_records (
            id, company_id, employee_id, area_id, task_id, record_date,
            start_time, end_time, hours, observations, created_at, updated_at,
            deleted_at, created_by, updated_by, deleted_by
        )
        SELECT
            id, company_id, employee_id, area_id, task_id, record_date,
            start_time, end_time, COALESCE(hours, 0), observations, created_at, updated_at,
            deleted_at, created_by, updated_by, deleted_by
        FROM time_records_old
        """
    )
    cur.execute("DROP TABLE time_records_old")
    cur.execute("PRAGMA foreign_keys=on")
    con.commit()
    con.close()
    print("time_records migrated.")


if __name__ == "__main__":
    main()
