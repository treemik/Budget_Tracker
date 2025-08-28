# Budget Tracker

A simple CLI budget tracker made using python and SQLite

## Features

Add income or expense with category, note, and date.
List with filters (category, type (income or expense), date range)
Monthly summaries (income, expense, balance, category breakdown)

## Installation
```bash
git clone
cd budget_tracker
python3 budget.py <command>
```
## Usage examples


#### Add an expense
```bash
python budget.py add -a 12.50 -c food -t expense -n "Lunch"
```
#### List all income entries
```bash
python budget.py list -t income
```
#### Show August 2025 summary
```bash
python budget.py summary -m 8 -y 2025
```

## Database

Creates budget.db automatically in the project folder
Stores entries with amounts (in cents), category, notes, date, and type (income or expense)

## Requirements

No external dependencies required 

## License

MIT