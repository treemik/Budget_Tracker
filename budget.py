import argparse
from datetime import datetime
import sqlite3




def parse_date(date_str):
    try:
        datetime.strptime(date_str, "%d.%m.%Y")
        return to_iso(date_str)
    except ValueError:
        raise argparse.ArgumentTypeError("%s is not a valid date. dd.mm.yyyy is required" % date_str)

def to_iso(date_str: str)->str:
    return datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")

def from_iso(date_str: str)->str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")

def to_int( amount_str):
    return int(round(float(amount_str)*100))

def to_string(amount,entry_type):
    if entry_type == "income":
        return f" ${amount/100:>10,.2f}"
    elif entry_type == "expense":
        return f"-${abs(amount)/100:>10,.2f}"
    else:
        raise ValueError (f"Unknown entry type {entry_type}")
# set up paser
parser=argparse.ArgumentParser(description="Track your budget from the command line")
subparsers=parser.add_subparsers(dest="command")
subparsers.required=True
# Set up add paser
add_parser=subparsers.add_parser("add",help="Add an income or expense to the database")
add_parser.add_argument("--amount","-a",type=to_int,required=True,help="Amount to add")
add_parser.add_argument("--category","-c",type=str,required=True,help="Category to add")
add_parser.add_argument("-n","--note",type=str,help="Note to add")
add_parser.add_argument("-d","--date",type=parse_date,help="Date to add")
add_parser.add_argument("-t","--entry_type",choices=["income","expense"],required=True,help="type must be income or expense")
#Set up list paser
list_parser=subparsers.add_parser("list",help="List all items in the database")
list_parser.add_argument("-c","--category",help="Filter by category")
list_parser.add_argument("-f","--date_from",type=parse_date,help="From date")
list_parser.add_argument("--date_to",type=parse_date,help="To date")
list_parser.add_argument("-t","--entry_type",choices=["income","expense"],help="income or expense")
#Set up summary parser
summary_parser=subparsers.add_parser("summary",help="Summarize a month's spending habits")
summary_parser.add_argument("-m","--month",choices=range(1,13), type=int,help="Month to summarize. defaults to current month")
summary_parser.add_argument("-y","--year",type=int,help="Year of month to summarize. defaults to current year")

args=parser.parse_args()



conn = sqlite3.connect("budget.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS entries (
id INTEGER PRIMARY KEY AUTOINCREMENT,
amount INTEGER NOT NULL,
category TEXT NOT NULL,
note TEXT,
date TEXT NOT NULL,
entry_type TEXT CHECK (entry_type in ('income','expense'))NOT NULL
)
""")
conn.close()

if args.command=="add":
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    if args.date is None:
        args.date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO entries (amount, category, note, date, entry_type) VALUES (?,?,?,?,?)",
        (args.amount, args.category, args.note, args.date, args.entry_type)
    )
    print (f"Added {to_string(args.amount,args.entry_type)} {args.category} {args.note} {from_iso(args.date)} {args.entry_type}")
    conn.commit()
    conn.close()

elif args.command=="list":
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    query = "SELECT id,amount, category, note, date, entry_type FROM entries"
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
    if args.entry_type:
        conditions.append("entry_type=?")
        params.append(args.entry_type)
    if conditions:
        query+=" WHERE "+" AND ".join(conditions)
    query+=" ORDER BY date DESC, id DESC"

    cursor.execute(query,params)
    rows = cursor.fetchall()


    if not rows:
        print(f"No entries found matching criteria {params}")
    else:
        print(f"{'ID':<4}{' AMOUNT':<12} {'CATEGORY':<13}{'NOTE':<20}{'DATE':<12}{'TYPE'}")
        print("-" * 68)
        for row in rows:

            id, amount, category, note, date, entry_type = row



            print(f"{id:<4}{to_string(amount,entry_type)} {category[:12]:<13}{note or '':<20}{from_iso(date):<12}{entry_type}")
    conn.close()

elif args.command=="summary":
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    if not args.year:
        args.year = datetime.now().year
    if not args.month:
        args.month = datetime.now().month

    start_date=datetime(args.year,args.month,1)
    if args.month<12:
        end_date=datetime(args.year,args.month+1,1)
    elif args.month==12:
        end_date=datetime(args.year+1,1,1)
    summary_month = start_date.strftime("%B %Y")
    start_date=start_date.strftime("%Y-%m-%d")
    end_date=end_date.strftime("%Y-%m-%d")
    date_filter="date>=? AND date<?"
    date_params=[start_date,end_date]

    query=f"SELECT SUM(amount) FROM entries WHERE {date_filter} AND entry_type='income'"
    cursor.execute(query,date_params)
    net_income = cursor.fetchone()[0] or 0
    query=f"SELECT SUM(amount) FROM entries WHERE {date_filter} AND entry_type='expense'"
    cursor.execute(query,date_params)
    net_expense = cursor.fetchone()[0] or 0
    net_total = net_income - net_expense
    if net_total >=0:
        entry_type='income'
    elif net_total < 0:
        entry_type='expense'
# expense set to income to display as positive by convention
    print("\n")
    title=f"SUMMARY - {summary_month}"
    length=len(title)

    print (title)
    print("-" * length+ "\n")

    print (f"{'INCOME':<13}{to_string(net_income,'income')}\n{'EXPENSES':<13}{to_string(net_expense,'income')}")
    print (f"{'BALANCE':<13}{to_string(net_total,entry_type)}")

    query=f"SELECT category, SUM(amount) FROM entries WHERE {date_filter} AND entry_type='expense' GROUP BY category ORDER BY SUM(amount) DESC"
    cursor.execute(query,date_params)
    rows = cursor.fetchall()
    if not rows:
        print("No expenses found for this period.")
    else:
        print("-" * 25)
        print("EXPENSES \n")

        print(f"{'CATEGORY':<13}{' AMOUNT':<12}  ")
        print("-"*25)
        for cat, total in rows:


            print(f"{cat[:12]:<13}{to_string(total,'income')}")
    conn.close()