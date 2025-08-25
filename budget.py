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
# set up paser
parser=argparse.ArgumentParser(description="Track your budget from the command line")
subparsers=parser.add_subparsers(dest="command")
# Set up add paser
add_parser=subparsers.add_parser("add",help="Add a budget to the database")
add_parser.add_argument("--amount","-a",type=to_int,required=True,help="Amount to add")
add_parser.add_argument("--category","-c",type=str,required=True,help="Category to add")
add_parser.add_argument("-n","--note",type=str,help="Note to add")
add_parser.add_argument("-d","--date",type=parse_date,help="Date to add")
add_parser.add_argument("-t","--type",choices=["income","expense"],required=True,help="income or expense")
#Set up list paser
list_parser=subparsers.add_parser("list",help="List all budgets")
list_parser.add_argument("-c","--category",)
list_parser.add_argument("-f","--date_from",type=parse_date,help="From date")
list_parser.add_argument("--date_to",type=parse_date,help="To date")
list_parser.add_argument("-t","--type",choices=["income","expense"],help="income or expense")
#Set up summary parser
summary_parser=subparsers.add_parser("summary",help="Summarize a budget")
summary_parser.add_argument("-m","--month",choices=range(1,13), type=int,help="Month to add")
summary_parser.add_argument("-y","--year",type=int,help="Year to add")

args=parser.parse_args()

if args.command is None:
    parser.print_help()
    exit()

conn = sqlite3.connect("budget.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS entries (
id INTEGER PRIMARY KEY AUTOINCREMENT,
amount INTEGER NOT NULL,
category TEXT NOT NULL,
note TEXT,
date TEXT NOT NULL,
type TEXT NOT NULL
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
    conn.close()

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
        print(f"{'ID':<4}{' AMOUNT':<12} {'CATEGORY':<13}{'NOTE':<20}{'DATE':<12}{'TYPE'}")
        print("-" * 68)
        for row in rows:

            id, amount, category, note, date, entry_type = row



            print(f"{id:<4}{to_string(amount,entry_type)} {category[:12]:<13}{note or '':<20}{from_iso(date):<12}{entry_type}")
    conn.close()

elif args.command=="summary":
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

    query=f"SELECT SUM(amount) FROM entries WHERE {date_filter} AND type='income'"
    cursor.execute(query,date_params)
    net_income = cursor.fetchone()[0] or 0
    query=f"SELECT SUM(amount) FROM entries WHERE {date_filter} AND type='expense'"
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

    query=f"SELECT category, SUM(amount) FROM entries WHERE {date_filter} AND type='expense' GROUP BY category ORDER BY SUM(amount) DESC"
    cursor.execute(query,date_params)
    rows = cursor.fetchall()
    if not rows:
        print("No entries found.")
    else:
        print("-" * 25)
        print("EXPENSES \n")

        print(f"{'CATEGORY':<13}{' AMOUNT':<12}  ")
        print("-"*25)
        for cat, total in rows:


            print(f"{cat[:12]:<13}{to_string(total,'income')}")
    conn.close()