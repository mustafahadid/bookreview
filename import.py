import csv
import psycopg2

db = psycopg2.connect("postgres://pvyirddicnfgsd:602964f074a8e32c131324c6e6331311c805881fa9c765127dca0171de4b6e11@ec2-52-70-15-120.compute-1.amazonaws.com:5432/d1kjt5t4kjtocu")
cursor = db.cursor()
cursor.execute("SELECT isbn, title, author, year FROM book")
with open('books.csv', 'r')as file:
    reader = csv.reader(file)

    next(reader)
    for row in reader:

        cursor.execute("INSERT INTO book(isbn, title, author, year)VALUES(%s, %s, %s, %s)", row)
        print(row)

db.commit()
print("DONE")
