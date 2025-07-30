import sqlite3
from datetime import datetime

DB_FILE = 'business.db'

SCHEMA_PRODUCTS = '''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    price REAL NOT NULL,
    description TEXT
);
'''

SCHEMA_TRANSACTIONS = '''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL, -- purchase, sale, commission
    date TEXT NOT NULL, -- YYYY-MM-DD
    product_id INTEGER,
    unit_price REAL,
    amount REAL,
    vendor TEXT,
    customer TEXT,
    user_id TEXT,
    raw_message TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
'''

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute(SCHEMA_PRODUCTS)
        conn.execute(SCHEMA_TRANSACTIONS)
        conn.commit()

def add_product(name, price, description=None):
    with get_db() as conn:
        conn.execute(
            'INSERT OR IGNORE INTO products (name, price, description) VALUES (?, ?, ?)',
            (name, price, description)
        )
        conn.commit()

def get_product_by_name(name):
    with get_db() as conn:
        cur = conn.execute('SELECT * FROM products WHERE name = ?', (name,))
        return cur.fetchone()

def list_products():
    with get_db() as conn:
        cur = conn.execute('SELECT * FROM products')
        return [dict(row) for row in cur.fetchall()]

def insert_transaction(data: dict):
    # Look up product_id if product name is provided
    product_id = None
    unit_price = None
    if data.get('product'):
        product = get_product_by_name(data['product'])
        if product:
            product_id = product['id']
            unit_price = product['price']
    with get_db() as conn:
        conn.execute(
            '''INSERT INTO transactions (type, date, product_id, unit_price, amount, vendor, customer, user_id, raw_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                data.get('type'),
                data.get('date', datetime.now().strftime('%Y-%m-%d')),
                product_id,
                unit_price,
                data.get('amount'),
                data.get('vendor'),
                data.get('customer'),
                data.get('user_id'),
                data.get('raw_message'),
            )
        )
        conn.commit()

def query_transactions(where_clause='', params=()):
    with get_db() as conn:
        cur = conn.execute(f'SELECT * FROM transactions {where_clause}', params)
        return [dict(row) for row in cur.fetchall()] 