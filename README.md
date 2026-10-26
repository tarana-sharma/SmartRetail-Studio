# SmartRetail Studio Enterprise Pro
### Modern Desktop Enterprise Resource Planning (ERP) & Interactive Analytics Suite

SmartRetail Studio is an enterprise-grade desktop ERP application engineered in Python with SQLite and ttkbootstrap.

---

## Features
- **Interactive Visual Analytics**: Interactive chart engine with dynamic metric toggling (Revenue, Units Sold, Gross Profit, Average Ticket), dynamic chart-type switching (Bar Chart, Trend Curve, Donut Share, Correlation Heatmap), and built-in Matplotlib pan/zoom/save toolbar.
- **Warehouse & Inventory Hub**: Full CRUD product registry connected to an ACID-compliant SQLite relational database, live instant filtering, inventory valuation, stock health tags, and safe foreign-key cascade deletions.
- **POS Checkout & Invoicing Terminal**: Catalog browser with live search, quantity controls, live cart calculation, instant stock deduction, and an itemized modal tax invoice with automatic disk receipt generation.

---

## Installation & Launch

1. **Activate Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows (PowerShell):
   venv\Scripts\Activate.ps1
   # macOS / Linux:
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**:
   ```bash
   python main.py
   ```
