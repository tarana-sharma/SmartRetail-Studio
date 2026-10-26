"""
High-Performance Business Intelligence Analytics Engine.
Processes relational SQL records into structured statistical dataframes.
"""
import pandas as pd
import numpy as np
from database.db_manager import DatabaseManager

class SalesAnalyticsEngine:
    def __init__(self):
        self.db = DatabaseManager()

    def get_sales_dataframe(self) -> pd.DataFrame:
        query = """
            SELECT 
                s.transaction_id,
                s.sale_date,
                p.category,
                p.name AS item_name,
                si.quantity AS units_sold,
                si.unit_price,
                si.line_total AS revenue,
                (si.unit_price - p.cost_price) * si.quantity AS profit
            FROM sale_items si
            JOIN sales s ON si.transaction_id = s.transaction_id
            JOIN products p ON si.item_id = p.item_id;
        """
        with self.db.get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        if df.empty:
            return pd.DataFrame(columns=[
                "transaction_id", "sale_date", "category", "item_name",
                "units_sold", "unit_price", "revenue", "profit"
            ])

        if df["units_sold"].isnull().any():
            median_val = df["units_sold"].median()
            df["units_sold"] = df["units_sold"].fillna(median_val)

        return df

    def get_summary_kpis(self) -> dict:
        df = self.get_sales_dataframe()
        if df.empty:
            return {
                "total_revenue": 0.0,
                "gross_profit": 0.0,
                "average_basket": 0.0,
                "total_transactions": 0,
                "lead_category": "N/A"
            }

        rev_arr = df["revenue"].to_numpy()
        profit_arr = df["profit"].to_numpy()
        
        return {
            "total_revenue": float(np.sum(rev_arr)),
            "gross_profit": float(np.sum(profit_arr)),
            "average_basket": float(np.mean(rev_arr)),
            "total_transactions": int(df["transaction_id"].nunique()),
            "lead_category": str(df.groupby("category")["revenue"].sum().idxmax()) if not df.empty else "N/A"
        }

    def get_category_aggregates(self) -> pd.DataFrame:
        df = self.get_sales_dataframe()
        if df.empty:
            return pd.DataFrame(columns=["category", "revenue", "profit", "units_sold"])
        return df.groupby("category").agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units_sold=("units_sold", "sum")
        ).reset_index()

    def get_correlation_matrix(self) -> pd.DataFrame:
        df = self.get_sales_dataframe()
        if df.empty or len(df) < 2:
            return pd.DataFrame()
        return df[["units_sold", "unit_price", "revenue", "profit"]].corr()
