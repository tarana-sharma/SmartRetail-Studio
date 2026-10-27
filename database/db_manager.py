"""
SQLite Database Layer.
Provides ACID transactions, relational foreign key constraints, and safe cascading deletion.
"""
import sqlite3
import os
from typing import List, Dict, Any

DB_PATH = os.path.join("data", "smart_retail.db")

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Products Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    item_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    cost_price REAL NOT NULL,
                    selling_price REAL NOT NULL,
                    stock_qty INTEGER NOT NULL CHECK(stock_qty >= 0)
                );
            """)

            # Sales Orders Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    transaction_id TEXT PRIMARY KEY,
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subtotal REAL NOT NULL,
                    tax_amount REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    payment_method TEXT DEFAULT 'Cash'
                );
            """)

            # Line Items Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sale_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    line_total REAL NOT NULL,
                    FOREIGN KEY (transaction_id) REFERENCES sales(transaction_id) ON DELETE CASCADE,
                    FOREIGN KEY (item_id) REFERENCES products(item_id) ON DELETE CASCADE
                );
            """)

            conn.commit()
            self._seed_sample_data(cursor, conn)

    def _seed_sample_data(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
        cursor.execute("SELECT COUNT(*) FROM products;")
        if cursor.fetchone()[0] == 0:
            catalog = [
                ("SKU-1001", "Logitech MX Master 3S Wireless Mouse", "Electronics", 5500.0, 8999.0, 24),
                ("SKU-1002", "Keychron K2 Mechanical Keyboard", "Electronics", 6200.0, 9499.0, 8),
                ("SKU-1003", "Sony WH-1000XM5 Noise-Cancelling Headphones", "Electronics", 18500.0, 26990.0, 12),
                ("SKU-1004", "Dell UltraSharp 27-inch 4K Monitor", "Electronics", 28000.0, 38500.0, 5),
                ("SKU-1005", "Classic Oxford Slim Fit Cotton Shirt", "Apparel", 950.0, 2199.0, 40),
                ("SKU-1006", "Levi's 511 Slim Fit Stretch Denim Jeans", "Apparel", 1400.0, 3299.0, 28),
                ("SKU-1007", "North Face Waterproof Windbreaker Jacket", "Apparel", 3400.0, 6899.0, 15),
                ("SKU-1008", "Raw Forest Organic Honey 500g", "Groceries", 220.0, 480.0, 35),
                ("SKU-1009", "Cold-Pressed Organic Extra Virgin Olive Oil 1L", "Groceries", 650.0, 1290.0, 18),
                ("SKU-1010", "California Whole Roasted Almonds 1kg", "Groceries", 520.0, 990.0, 22),
                ("SKU-1011", "Ceramic Pour-Over Coffee Dripper Set", "Home & Living", 700.0, 1450.0, 14),
                ("SKU-1012", "Minimalist Matte Aluminum LED Desk Lamp", "Home & Living", 1100.0, 2490.0, 6)
            ]
            cursor.executemany("""
                INSERT INTO products (item_id, name, category, cost_price, selling_price, stock_qty)
                VALUES (?, ?, ?, ?, ?, ?);
            """, catalog)

            sales_records = [
                ("ORD-7001", 17998.0, 3239.64, 21237.64, "Credit Card"),
                ("ORD-7002", 9499.0, 1709.82, 11208.82, "UPI"),
                ("ORD-7003", 5498.0, 989.64, 6487.64, "Cash"),
                ("ORD-7004", 38500.0, 6930.00, 45430.00, "Credit Card"),
                ("ORD-7005", 2760.0, 496.80, 3256.80, "UPI"),
                ("ORD-7006", 6899.0, 1241.82, 8140.82, "Debit Card"),
                ("ORD-7007", 26990.0, 4858.20, 31848.20, "Credit Card")
            ]
            cursor.executemany("""
                INSERT INTO sales (transaction_id, subtotal, tax_amount, total_amount, payment_method)
                VALUES (?, ?, ?, ?, ?);
            """, sales_records)

            line_items = [
                ("ORD-7001", "SKU-1001", 2, 8999.0, 17998.0),
                ("ORD-7002", "SKU-1002", 1, 9499.0, 9499.0),
                ("ORD-7003", "SKU-1005", 1, 2199.0, 2199.0),
                ("ORD-7003", "SKU-1006", 1, 3299.0, 3299.0),
                ("ORD-7004", "SKU-1004", 1, 38500.0, 38500.0),
                ("ORD-7005", "SKU-1008", 2, 480.0, 960.0),
                ("ORD-7005", "SKU-1009", 1, 1290.0, 1290.0),
                ("ORD-7006", "SKU-1007", 1, 6899.0, 6899.0),
                ("ORD-7007", "SKU-1003", 1, 26990.0, 26990.0)
            ]
            cursor.executemany("""
                INSERT INTO sale_items (transaction_id, item_id, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?);
            """, line_items)

            conn.commit()

    def add_or_update_product(self, item_id: str, name: str, category: str, cost: float, price: float, qty: int) -> None:
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO products (item_id, name, category, cost_price, selling_price, stock_qty)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    name=excluded.name,
                    category=excluded.category,
                    cost_price=excluded.cost_price,
                    selling_price=excluded.selling_price,
                    stock_qty=excluded.stock_qty;
            """, (item_id, name, category, cost, price, qty))
            conn.commit()

    def fetch_all_products(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY category ASC, name ASC;")
            return [dict(row) for row in cursor.fetchall()]

    def restock_product(self, item_id: str, additional_qty: int) -> int:
        """Adds incoming units directly to existing stock."""
        with self.get_connection() as conn:
            conn.execute("UPDATE products SET stock_qty = stock_qty + ? WHERE item_id = ?;", (additional_qty, item_id))
            conn.commit()
            cursor = conn.cursor()
            cursor.execute("SELECT stock_qty FROM products WHERE item_id = ?;", (item_id,))
            row = cursor.fetchone()
            return row["stock_qty"] if row else 0

    def delete_product(self, item_id: str) -> None:
        """Safely removes an item and its associated line items to satisfy foreign key rules."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM sale_items WHERE item_id = ?;", (item_id,))
            conn.execute("DELETE FROM products WHERE item_id = ?;", (item_id,))
            conn.commit()

    def record_sale_transaction(self, tx_id: str, cart_items: List[Any], subtotal: float, tax: float, grand_total: float, payment_method: str = "Card") -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                for item in cart_items:
                    cursor.execute("SELECT stock_qty, name FROM products WHERE item_id = ?;", (item.product.item_id,))
                    row = cursor.fetchone()
                    if not row or row["stock_qty"] < item.quantity:
                        raise ValueError(f"Insufficient stock for '{item.product.name}'. Available: {row['stock_qty'] if row else 0}")

                    cursor.execute("""
                        UPDATE products
                        SET stock_qty = stock_qty - ?
                        WHERE item_id = ?;
                    """, (item.quantity, item.product.item_id))

                cursor.execute("""
                    INSERT INTO sales (transaction_id, subtotal, tax_amount, total_amount, payment_method)
                    VALUES (?, ?, ?, ?, ?);
                """, (tx_id, subtotal, tax, grand_total, payment_method))

                for item in cart_items:
                    cursor.execute("""
                        INSERT INTO sale_items (transaction_id, item_id, quantity, unit_price, line_total)
                        VALUES (?, ?, ?, ?, ?);
                    """, (tx_id, item.product.item_id, item.quantity, item.product.get_selling_price(), item.get_subtotal()))

                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e
