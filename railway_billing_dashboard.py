"""
Building a Relational Railway Network & Train Stop Billing Dashboard
--------------------------------------------------------------------
DBMS Project  |  Python + SQLite + Tkinter

Tables (one-to-many chain):
    Zones (1) ---< Train_Services (1) ---< Stop_Allocations
"""


import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

DB_NAME = "railway_network.db"

# Global handles used by the GUI (filled in by build_gui)
conn = None
widgets = {}
input_vars = {}     # StringVar objects for the four insert fields


# =====================================================================
# SECTION 1 - DATABASE LAYER 
# =====================================================================

def get_connection(db_name=DB_NAME):
    """Open the SQLite database and switch ON foreign key enforcement.
    SQLite ignores FOREIGN KEY rules unless this PRAGMA is set for
    every new connection."""
    connection = sqlite3.connect(db_name)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def perform_select(connection, sql, params=()):
    """Run a SELECT with ? placeholders and return all rows.
    No commit is needed because a SELECT does not change data."""
    cursor = connection.cursor()
    cursor.execute(sql, params)
    return cursor.fetchall()


def perform_write(connection, sql, params=()):
    """Run an INSERT / DELETE with ? placeholders, then commit."""
    cursor = connection.cursor()
    cursor.execute(sql, params)
    connection.commit()


def create_tables(connection):
    """Create the three tables if they do not already exist."""
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Zones (
            Zone_ID       INTEGER PRIMARY KEY AUTOINCREMENT,
            Zone_Name     TEXT NOT NULL UNIQUE,
            Contact_Email TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Train_Services (
            Service_ID   INTEGER PRIMARY KEY AUTOINCREMENT,
            Zone_ID      INTEGER NOT NULL,
            Train_Name   TEXT NOT NULL,
            Service_Date TEXT,
            FOREIGN KEY (Zone_ID) REFERENCES Zones(Zone_ID)
                ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Stop_Allocations (
            Allocation_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Service_ID    INTEGER NOT NULL,
            Station_Name  TEXT NOT NULL,
            Fare_Amount   REAL NOT NULL CHECK (Fare_Amount >= 0),
            FOREIGN KEY (Service_ID) REFERENCES Train_Services(Service_ID)
                ON DELETE CASCADE
        )
    """)
    connection.commit()


def database_is_empty(connection):
    """True only when all three tables contain no rows."""
    for table in ("Zones", "Train_Services", "Stop_Allocations"):
        count = perform_select(connection, f"SELECT COUNT(*) FROM {table}")[0][0]
        if count > 0:
            return False
    return True


def insert_sample_data(connection):
    """Insert sample rows ONLY if the database is completely empty."""
    if not database_is_empty(connection):
        return False
    cursor = connection.cursor()
    zones = [
        ("Southern Railway", "contact@sr.example.in"),
        ("Western Railway", "contact@wr.example.in"),
    ]
    cursor.executemany(
        "INSERT INTO Zones (Zone_Name, Contact_Email) VALUES (?, ?)", zones)

    services = [
        (1, "Chennai Express", "2026-11-01"),
        (1, "Nilgiri Express", "2026-11-02"),
        (2, "Mumbai Rajdhani", "2026-11-03"),
    ]
    cursor.executemany(
        "INSERT INTO Train_Services (Zone_ID, Train_Name, Service_Date) "
        "VALUES (?, ?, ?)", services)

    stops = [
        (1, "Katpadi", 150.00),
        (1, "Chennai Central", 320.50),
        (2, "Coimbatore", 275.00),
        (3, "Surat", 410.00),
        (3, "Mumbai Central", 560.75),
    ]
    cursor.executemany(
        "INSERT INTO Stop_Allocations (Service_ID, Station_Name, Fare_Amount) "
        "VALUES (?, ?, ?)", stops)
    connection.commit()
    return True


# ---------- INSERT logic ----------

def validate_inputs(zone, train, station, fare_text):
    """Return (True, fare_float, '') or (False, None, error_message)."""
    if not zone.strip() or not train.strip() or not station.strip() \
            or not fare_text.strip():
        return False, None, "All fields are required. Please fill in every field."
    try:
        fare = float(fare_text.strip())
    except ValueError:
        return False, None, "Fare Amount must be a number (e.g. 250 or 250.50)."
    if fare != fare or fare in (float("inf"), float("-inf")):
        return False, None, "Fare Amount must be a valid finite number."
    if fare < 0:
        return False, None, "Fare Amount cannot be negative."
    return True, fare, ""


def find_zone_id(connection, zone_name):
    """Return the Zone_ID of an existing zone (case-insensitive) or None."""
    rows = perform_select(
        connection,
        "SELECT Zone_ID FROM Zones WHERE Zone_Name = ? COLLATE NOCASE",
        (zone_name.strip(),))
    return rows[0][0] if rows else None


def add_stop_record(connection, zone, train, station, fare):
    """Zone -> Service -> Stop insert done as ONE transaction.
    If any step fails, rollback leaves the database unchanged."""
    try:
        cursor = connection.cursor()
        zone_id = find_zone_id(connection, zone)
        created_zone = False
        if zone_id is None:                       # zone does not exist yet
            cursor.execute(
                "INSERT INTO Zones (Zone_Name, Contact_Email) VALUES (?, ?)",
                (zone.strip(), None))
            zone_id = cursor.lastrowid
            created_zone = True

        cursor.execute(
            "INSERT INTO Train_Services (Zone_ID, Train_Name, Service_Date) "
            "VALUES (?, ?, ?)",
            (zone_id, train.strip(), date.today().isoformat()))
        service_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO Stop_Allocations (Service_ID, Station_Name, Fare_Amount) "
            "VALUES (?, ?, ?)",
            (service_id, station.strip(), fare))
        allocation_id = cursor.lastrowid

        connection.commit()                       # make everything permanent
        return zone_id, service_id, allocation_id, created_zone
    except sqlite3.Error:
        connection.rollback()                     # undo partial work
        raise


# ---------- SELECT logic ----------

def fetch_zones(connection):
    return perform_select(
        connection,
        "SELECT Zone_ID, Zone_Name, Contact_Email FROM Zones ORDER BY Zone_ID")


def fetch_services(connection):
    return perform_select(
        connection,
        "SELECT Service_ID, Zone_ID, Train_Name, Service_Date "
        "FROM Train_Services ORDER BY Service_ID")


def fetch_stops(connection):
    return perform_select(
        connection,
        "SELECT Allocation_ID, Service_ID, Station_Name, Fare_Amount "
        "FROM Stop_Allocations ORDER BY Allocation_ID")


def fetch_combined(connection):
    """JOIN across all three tables for the Combined View tab."""
    return perform_select(connection, """
        SELECT ts.Service_ID, z.Zone_Name, ts.Train_Name, ts.Service_Date,
               sa.Station_Name, sa.Fare_Amount
        FROM Stop_Allocations sa
        JOIN Train_Services ts ON sa.Service_ID = ts.Service_ID
        JOIN Zones z           ON ts.Zone_ID    = z.Zone_ID
        ORDER BY ts.Service_ID, sa.Allocation_ID
    """)


# ---------- DELETE logic ----------

def delete_zone(connection, zone_id):
    """Children (services, stops) are removed by ON DELETE CASCADE."""
    perform_write(connection, "DELETE FROM Zones WHERE Zone_ID = ?", (zone_id,))


def delete_service(connection, service_id):
    """Its stop allocations are removed by ON DELETE CASCADE."""
    perform_write(
        connection, "DELETE FROM Train_Services WHERE Service_ID = ?",
        (service_id,))


def delete_stop(connection, allocation_id):
    """Only the stop is removed; parent service and zone stay."""
    perform_write(
        connection, "DELETE FROM Stop_Allocations WHERE Allocation_ID = ?",
        (allocation_id,))


# =====================================================================
# SECTION 2 - GUI LAYER (Tkinter)
# =====================================================================

def fill_tree(tree, rows):
    """Clear a Treeview and fill it with fresh rows."""
    for item in tree.get_children():
        tree.delete(item)
    for row in rows:
        tree.insert("", tk.END, values=row)


def make_tree(parent, columns, widths):
    """Create a Treeview with a vertical scrollbar."""
    frame = ttk.Frame(parent)
    frame.pack(fill=tk.BOTH, expand=True)
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for col, width in zip(columns, widths):
        tree.heading(col, text=col.replace("_", " "))
        tree.column(col, width=width, anchor=tk.CENTER)
    scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    return tree


def refresh_all():
    """Reload the four tabs and the three delete dropdowns."""
    fill_tree(widgets["tree_combined"], fetch_combined(conn))
    fill_tree(widgets["tree_zones"], fetch_zones(conn))
    fill_tree(widgets["tree_services"], fetch_services(conn))
    fill_tree(widgets["tree_stops"], fetch_stops(conn))

    # Dropdown text looks like "3 - Mumbai Rajdhani"; the ID is before " - "
    widgets["cb_zone"]["values"] = [f"{r[0]} - {r[1]}" for r in fetch_zones(conn)]
    widgets["cb_service"]["values"] = [
        f"{r[0]} - {r[2]} (Zone {r[1]})" for r in fetch_services(conn)]
    widgets["cb_stop"]["values"] = [
        f"{r[0]} - {r[2]} (Service {r[1]}, Rs {r[3]:.2f})"
        for r in fetch_stops(conn)]
    # Clear old selections so deleted IDs are never kept
    for key in ("cb_zone", "cb_service", "cb_stop"):
        widgets[key].set("")


def on_insert():
    """Insert button handler: validate, then write to the database."""
    zone = input_vars["e_zone"].get()
    train = input_vars["e_train"].get()
    station = input_vars["e_station"].get()
    fare_text = input_vars["e_fare"].get()

    ok, fare, error = validate_inputs(zone, train, station, fare_text)
    if not ok:
        messagebox.showerror("Invalid Input", error)
        return
    try:
        zone_id, service_id, alloc_id, created = add_stop_record(
            conn, zone, train, station, fare)
    except sqlite3.Error as err:
        messagebox.showerror("Database Error", f"Insert failed:\n{err}")
        return

    zone_msg = "New zone created" if created else "Existing zone used"
    messagebox.showinfo(
        "Success",
        f"{zone_msg} (Zone_ID {zone_id}).\n"
        f"Service_ID {service_id} and Allocation_ID {alloc_id} added.")
    for key in ("e_zone", "e_train", "e_station", "e_fare"):
        input_vars[key].set("")
    refresh_all()


def selected_id(combo_key):
    """Read the ID from the chosen dropdown item, or None if nothing chosen."""
    text = widgets[combo_key].get()
    if not text:
        return None
    return int(text.split(" - ")[0])


def on_delete(combo_key, label, delete_function, warning):
    """Generic handler for the three Delete Selected buttons."""
    record_id = selected_id(combo_key)
    if record_id is None:
        messagebox.showwarning("Nothing Selected", f"Please select a {label} first.")
        return
    if not messagebox.askyesno("Confirm Delete",
                               f"Delete {label} {record_id}?\n{warning}"):
        return
    try:
        delete_function(conn, record_id)
    except sqlite3.Error as err:
        conn.rollback()
        messagebox.showerror("Database Error", f"Delete failed:\n{err}")
        return
    messagebox.showinfo("Deleted", f"{label} {record_id} deleted.")
    refresh_all()


def build_gui(root):
    """Create the Insert panel, Delete panel and tabbed display."""
    root.title("Railway Network & Train Stop Billing Dashboard")
    root.geometry("1050x720")
    ttk.Style().theme_use("clam")

    ttk.Label(root, text="Railway Network & Train Stop Billing Dashboard",
              font=("Segoe UI", 16, "bold")).pack(pady=8)

    top = ttk.Frame(root)
    top.pack(fill=tk.X, padx=10)

    # ---- A. Insert panel ----
    insert_frame = ttk.LabelFrame(top, text="Insert Panel", padding=10)
    insert_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    fields = [("Zone Name", "e_zone"), ("Train Name", "e_train"),
              ("Station Name", "e_station"), ("Fare Amount", "e_fare")]
    for i, (label, key) in enumerate(fields):
        ttk.Label(insert_frame, text=label + ":").grid(
            row=i, column=0, sticky="w", pady=4)
        input_vars[key] = tk.StringVar()
        entry = ttk.Entry(insert_frame, width=30, textvariable=input_vars[key])
        entry.grid(row=i, column=1, pady=4, padx=6)
        widgets[key] = entry
    ttk.Button(insert_frame, text="Insert Record", command=on_insert).grid(
        row=len(fields), column=0, columnspan=2, pady=8)

    # ---- B. Delete panel ----
    delete_frame = ttk.LabelFrame(top, text="Delete Panel", padding=10)
    delete_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
    delete_items = [
        ("Railway Zone", "cb_zone", delete_zone,
         "This also deletes its train services and stop allocations."),
        ("Train Service", "cb_service", delete_service,
         "This also deletes its stop allocations."),
        ("Stop Allocation", "cb_stop", delete_stop,
         "Parent service and zone are not affected."),
    ]
    for i, (label, key, func, warning) in enumerate(delete_items):
        ttk.Label(delete_frame, text=label + ":").grid(
            row=i, column=0, sticky="w", pady=4)
        combo = ttk.Combobox(delete_frame, width=38, state="readonly")
        combo.grid(row=i, column=1, pady=4, padx=6)
        widgets[key] = combo
        ttk.Button(
            delete_frame, text="Delete Selected",
            command=lambda k=key, l=label, f=func, w=warning:
                on_delete(k, l, f, w)).grid(row=i, column=2, padx=4)

    # ---- C. Tabbed display ----
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tab_defs = [
        ("Combined View", "tree_combined",
         ("Service_ID", "Zone_Name", "Train_Name", "Service_Date",
          "Station_Name", "Fare_Amount"), (90, 170, 170, 110, 170, 100)),
        ("Zones", "tree_zones",
         ("Zone_ID", "Zone_Name", "Contact_Email"), (100, 250, 300)),
        ("Train Services", "tree_services",
         ("Service_ID", "Zone_ID", "Train_Name", "Service_Date"),
         (100, 100, 250, 150)),
        ("Stop Allocations", "tree_stops",
         ("Allocation_ID", "Service_ID", "Station_Name", "Fare_Amount"),
         (120, 100, 250, 120)),
    ]
    for title, key, columns, col_widths in tab_defs:
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=title)
        widgets[key] = make_tree(tab, columns, col_widths)

    refresh_all()


def main():
    """Start-up: connect, create tables, add sample data if empty, open GUI."""
    global conn
    try:
        conn = get_connection()
        create_tables(conn)
        insert_sample_data(conn)
    except sqlite3.Error as err:
        messagebox.showerror("Database Error", f"Could not start database:\n{err}")
        return
    root = tk.Tk()
    build_gui(root)
    root.mainloop()
    conn.close()


if __name__ == "__main__":
    main()

