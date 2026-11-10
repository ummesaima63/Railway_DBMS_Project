# Railway Network & Train Stop Billing Dashboard

## Project Overview
The Railway Network & Train Stop Billing Dashboard is a database management system developed using Python and SQLite. It helps manage railway zones, train services, stop allocations and fare details through a graphical user interface.

## Problem Statement
Traditional railway record management using spreadsheets can lead to data duplication, inconsistent records and difficulties in maintaining relationships between railway zones, train services and station allocations.

The project aims to develop a relational database management system that organizes railway information, manages fare details and allows users to insert, view and delete records efficiently through a graphical user interface.

## Technologies Used
- Python
- SQLite
- Tkinter (GUI)

## Main Features
1. **Railway Zones:** Store and manage railway zone details.
2. **Train Services:** Maintain train names and service dates.
3. **Stop Allocations:** Manage railway stations assigned to train services.
4. **Fare Management:** Store and manage fare amounts.
5. **Combined View:** Display railway information from multiple tables using SQL JOIN.
6. **Insert Records:** Add new records to the database.
7. **Delete Records:** Delete selected records.
8. **Input Validation:** Prevent invalid or incomplete entries.

## Database Structure
The project uses three main tables:

- Zones
- Train_Services
- Stop_Allocations

The tables are connected using primary keys and foreign keys to maintain relationships between records.

## Project Files
- `railway_billing_dashboard.py` – Main Python application.
- `railway_network.db` – SQLite database containing railway records.

## How to Run
1. Install Python.
2. Open the project folder in Visual Studio Code.
3. Open the terminal.
4. Run the following command:

```bash
uv run python railway_billing_dashboard.py
```

5. The Railway Network & Train Stop Billing Dashboard will open.

## Conclusion
This project demonstrates the practical application of DBMS concepts, relational database design, SQL queries, data management and Python GUI development.
