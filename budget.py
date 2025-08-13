import argparse
from datetime import datetime
import sqlite3

def parse_date(date_str):
    datetime.strptime(date_str, "%d.%m.%Y")
    return to_iso(date_str)

def to_iso(date_str: str)->str:
    return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")

def from_iso(date_str: str)->str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
# set up paser
parser=argparse.ArgumentParser(description="Track your budget from the command line")
subparsers=parser.add_subparsers(dest="command")
# Set up add paser
add_parser=subparsers.add_parser("add",help="Add a budget to the database")
add_parser.add_argument("--amount","-a",type=float,required=True,help="Amount to add")
add_parser.add_argument("--category","-c",type=str,required=True,help="Category to add")
add_parser.add_argument("-n","--note",type=str,help="Note to add")
add_parser.add_argument("-d","--date",type=parse_date,help="Date to add")
add_parser.add_argument("-t","--type",choices=["income","expense"],required=True,help="income or expense")
#Set up list paser
list_parser=subparsers.add_parser("list",help="List all budgets")
list_parser.add_argument("-c","--category",)
list_parser.add_argument("-f","--date_from",type=parse_date,help="From date")
list_parser.add_argument("-dt","--date_to",type=parse_date,help="To date")
list_parser.add_argument("-t","--type",choices=["income","expense"],help="income or expense")
#Set up summary parser
summary_parser=subparsers.add_parser("summary",help="Summarize a budget")

args=parser.parse_args()

conn = sqlite3.connect("budget.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS entries (
id INTEGER PRIMARY KEY AUTOINCREMENT,
amount REAL NOT NULL,
category TEXT NOT NULL,
note TEXT,
date TEXT NOT NULL,
type Text NOT NULL
)
""")

if args.command=="add":
    if args.date is None:
        args.date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO entries (amount, category, note, date, type) VALUES (?,?,?,?,?)",
        (args.amount, args.category, args.note, args.date, args.type)
    )
    conn.commit()
elif args.command=="list":
    query = "SELECT id,amount, category, note, date, type FROM entries"
    conditions=[]
    params=[]
    if args.category:
        conditions.append("category=?")
        params.append(args.category)
    if args.date_from:
        conditions.append("date>=?")
        params.append(args.date_from)
    if args.date_to:
        conditions.append("date<=?")
        params.append(args.date_to)
    if args.type:
        conditions.append("type=?")
        params.append(args.type)
    if conditions:
        query+=" WHERE "+" AND ".join(conditions)
    query+=" ORDER BY date DESC"

    cursor.execute(query,params)
    rows = cursor.fetchall()


    if not rows:
        print("No entries found.")
    else:
        print(f"{'ID':<4}{'AMOUNT':<8}{'CATEGORY':<13}{'NOTE':<20}{'DATE':<12}{'TYPE'}")
        print("-" * 60)
        for row in rows:
            id, amount, category, note, date, entry_type = row
            print(f"{id:<4}${amount:<8.2f}{category[:12]:<13}{note or '':<20}{from_iso(date):<12}{entry_type}")

elif args.command=="summary":
    cursor.execute("SELECT SUM(amount) FROM entries WHERE type='income'")
    net_income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM entries WHERE type='expense'")
    net_expense = cursor.fetchone()[0] or 0
    net_total = net_income - net_expense
    print (f"Income    ${net_income:<8.2f}\nExpenses -${net_expense:<8.2f}")
    print (f"Balance   ${net_total:<8.2f}")
    cursor.execute("SELECT category, SUM(amount) FROM entries WHERE type='expense' GROUP BY category ORDER BY SUM(amount) DESC")
    rows = cursor.fetchall()
    if not rows:
        print("No entries found.")
    else:
        for cat, total in rows:
            print(f"{cat[:12]:<13}${total:<8.2f}")