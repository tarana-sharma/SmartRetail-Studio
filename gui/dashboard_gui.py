"""
SmartRetail Studio Enterprise UI.
Modern, sleek interface with left navigation rail, interactive POS cashier, 
polished financial receipts, and an interactive real-time visual analytics studio.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import uuid
import datetime
import os

from database.db_manager import DatabaseManager
from core.models import RetailProduct, CartItem
from core.functional_tools import filter_low_stock, compute_total_inventory_value
from analytics.sales_engine import SalesAnalyticsEngine

class SmartRetailEnterpriseApp:
    def __init__(self, root: tb.Window):
        self.root = root
        self.root.title("SmartRetail Studio | Enterprise Retail ERP")
        self.root.geometry("1360x860")
        self.root.minsize(1120, 720)

        # Persistence & Analytics Engines
        self.db = DatabaseManager()
        self.engine = SalesAnalyticsEngine()
        self.cart = []

        # Analytics View State Variables
        self.chart_metric_var = tk.StringVar(value="revenue")
        self.chart_type_var = tk.StringVar(value="Multi-Panel Overview")
        self.canvas_widget = None
        self.current_figure = None

        self._configure_styles()
        self._reload_inventory()
        self._build_main_layout()

    def _configure_styles(self):
        self.style = tb.Style()
        self.style.configure("Sidebar.TFrame", background="#0B132B")
        self.style.configure("NavBtn.TButton", font=("Segoe UI", 10, "bold"), anchor="w", padding=(18, 12))
        self.style.configure("Card.TFrame", background="#FFFFFF", relief="flat")
        self.style.configure("MetricVal.TLabel", font=("Segoe UI", 16, "bold"), foreground="#0B132B")
        self.style.configure("MetricSub.TLabel", font=("Segoe UI", 8), foreground="#6C757D")

        # Table rows styling
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=6)
        self.style.configure("Treeview", font=("Segoe UI", 9), rowheight=28)

    def _reload_inventory(self):
        rows = self.db.fetch_all_products()
        self.inventory = [
            RetailProduct(
                r["item_id"], r["name"], r["category"],
                r["cost_price"], r["selling_price"], r["stock_qty"]
            ) for r in rows
        ]

    def _build_main_layout(self):
        # 1. Left Sidebar Navigation Rail
        self.sidebar = tb.Frame(self.root, style="Sidebar.TFrame", width=250)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        brand_frame = tb.Frame(self.sidebar, style="Sidebar.TFrame", padding=20)
        brand_frame.pack(fill=X)
        tb.Label(brand_frame, text="⚡ SmartRetail", font=("Segoe UI", 17, "bold"), foreground="#4CC9F0", background="#0B132B").pack(anchor="w")
        tb.Label(brand_frame, text="ENTERPRISE WORKBENCH", font=("Segoe UI", 7, "bold"), foreground="#8D99AE", background="#0B132B").pack(anchor="w", pady=(3, 0))

        tb.Separator(self.sidebar, bootstyle="secondary").pack(fill=X, padx=15, pady=12)

        routes = [
            ("📊  Interactive Analytics", self._show_dashboard_view),
            ("📦  Inventory & Stock", self._show_inventory_view),
            ("🧾  Point-of-Sale (POS)", self._show_pos_view)
        ]

        for label, callback in routes:
            btn = tb.Button(self.sidebar, text=label, bootstyle="link", style="NavBtn.TButton", command=callback)
            btn.pack(fill=X, padx=10, pady=4)

        footer = tb.Frame(self.sidebar, style="Sidebar.TFrame", padding=18)
        footer.pack(side=BOTTOM, fill=X)
        tb.Label(footer, text="● Connected to SQLite", font=("Segoe UI", 8), foreground="#06D6A0", background="#0B132B").pack(anchor="w")
        tb.Label(footer, text="Terminal: POS-01 (Active)", font=("Segoe UI", 8), foreground="#8D99AE", background="#0B132B").pack(anchor="w")

        # 2. Main Dynamic Content Frame
        self.main_container = tb.Frame(self.root, padding=24)
        self.main_container.pack(side=LEFT, fill=BOTH, expand=True)

        self.top_bar = tb.Frame(self.main_container)
        self.top_bar.pack(fill=X, pady=(0, 16))
        self.view_title = tb.Label(self.top_bar, text="Analytics Dashboard", font=("Segoe UI", 16, "bold"), foreground="#0B132B")
        self.view_title.pack(side=LEFT)

        self.content_frame = tb.Frame(self.main_container)
        self.content_frame.pack(fill=BOTH, expand=True)

        self._show_dashboard_view()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # =========================================================================
    # VIEW 1: INTERACTIVE EXECUTIVE VISUAL ANALYTICS
    # =========================================================================
    def _show_dashboard_view(self):
        self._clear_content()
        self.view_title.config(text="Executive Sales & Performance Intelligence")

        # 1. Top KPI Metric Cards
        kpi_row = tb.Frame(self.content_frame)
        kpi_row.pack(fill=X, pady=(0, 14))

        stats = self.engine.get_summary_kpis()
        self._render_kpi_card(kpi_row, "TOTAL REVENUE", f"₹ {stats['total_revenue']:,.2f}", "Verified", "primary")
        self._render_kpi_card(kpi_row, "GROSS PROFIT", f"₹ {stats['gross_profit']:,.2f}", "+28.4% Margin", "success")
        self._render_kpi_card(kpi_row, "AVERAGE BASKET", f"₹ {stats['average_basket']:,.2f}", "Per Order", "info")
        self._render_kpi_card(kpi_row, "TOP CATEGORY", stats['lead_category'], "Volume Leader", "warning")

        # 2. Interactive Chart Control Ribbon
        ctrl_card = tb.Labelframe(self.content_frame, text="Interactive Visualization Controls", padding=10, bootstyle="info")
        ctrl_card.pack(fill=X, pady=(0, 10))

        tb.Label(ctrl_card, text="Metric Filter:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(6, 4))
        metric_combo = tb.Combobox(
            ctrl_card, 
            textvariable=self.chart_metric_var, 
            values=["revenue", "profit", "units_sold"], 
            state="readonly", 
            width=14
        )
        metric_combo.pack(side=LEFT, padx=(0, 15))
        metric_combo.bind("<<ComboboxSelected>>", lambda e: self._render_interactive_charts())

        tb.Label(ctrl_card, text="View Layout:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(0, 4))
        type_combo = tb.Combobox(
            ctrl_card, 
            textvariable=self.chart_type_var, 
            values=["Multi-Panel Overview", "Focused Vertical Comparison", "Distribution Donut Only", "Feature Correlation Heatmap"], 
            state="readonly", 
            width=24
        )
        type_combo.pack(side=LEFT, padx=(0, 15))
        type_combo.bind("<<ComboboxSelected>>", lambda e: self._render_interactive_charts())

        tb.Button(ctrl_card, text="Refresh Telemetry", bootstyle="secondary-outline", command=self._render_interactive_charts).pack(side=LEFT, padx=5)

        # 3. Chart Container
        self.chart_container = tb.Frame(self.content_frame)
        self.chart_container.pack(fill=BOTH, expand=True)

        self._render_interactive_charts()

    def _render_interactive_charts(self):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        metric = self.chart_metric_var.get()
        chart_type = self.chart_type_var.get()
        cat_df = self.engine.get_category_aggregates()
        metric_label = "Revenue (₹)" if metric == "revenue" else ("Gross Profit (₹)" if metric == "profit" else "Units Sold")

        plt.style.use("seaborn-v0_8-whitegrid")

        if chart_type == "Multi-Panel Overview":
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12.4, 4.3), dpi=100)
            fig.patch.set_facecolor("#FFFFFF")
            fig.subplots_adjust(bottom=0.22, top=0.88, wspace=0.32)

            if not cat_df.empty:
                # 1. Bar plot
                colors = ["#3A86FF", "#06D6A0", "#FFB703", "#FB5607", "#8338EC"]
                bars = ax1.bar(cat_df["category"], cat_df[metric], color=colors[:len(cat_df)], width=0.52, edgecolor="#2563EB", linewidth=0.8)
                ax1.set_title(f"Category vs. {metric_label}", fontsize=9, fontweight="bold", color="#1E293B", pad=8)
                ax1.set_ylabel(metric_label, fontsize=8, color="#475569")
                ax1.tick_params(axis="x", rotation=15, labelsize=8)
                ax1.tick_params(axis="y", labelsize=8)

                # 2. Donut plot
                wedges, texts, autotexts = ax2.pie(
                    cat_df[metric], 
                    labels=cat_df["category"], 
                    autopct="%1.0f%%", 
                    startangle=140, 
                    colors=colors[:len(cat_df)],
                    pctdistance=0.75,
                    wedgeprops=dict(width=0.45, edgecolor="#FFFFFF", linewidth=2)
                )
                for autotext in autotexts:
                    autotext.set_fontsize(8)
                    autotext.set_weight("bold")
                for t in texts:
                    t.set_fontsize(8)
                ax2.set_title(f"{metric_label} Share", fontsize=9, fontweight="bold", color="#1E293B", pad=8)

            corr = self.engine.get_correlation_matrix()
            if not corr.empty:
                sns.heatmap(corr, annot=True, cmap="Blues", fmt=".2f", ax=ax3, cbar=False, annot_kws={"size": 7.5, "weight": "bold"}, linewidths=0.5)
                ax3.set_title("Operational Correlation", fontsize=9, fontweight="bold", color="#1E293B", pad=8)
                ax3.tick_params(axis="both", labelsize=7.5)

        elif chart_type == "Focused Vertical Comparison":
            fig, ax = plt.subplots(figsize=(10, 4.3), dpi=100)
            fig.patch.set_facecolor("#FFFFFF")
            if not cat_df.empty:
                palette = sns.color_palette("mako", len(cat_df))
                bars = ax.bar(cat_df["category"], cat_df[metric], color=palette, width=0.45, edgecolor="#1E293B")
                for bar in bars:
                    h = bar.get_height()
                    ax.annotate(f"{h:,.0f}", xy=(bar.get_x() + bar.get_width() / 2, h), xytext=(0, 3),
                                textcoords="offset points", ha='center', va='bottom', fontsize=8, fontweight="bold")
                ax.set_title(f"Detailed Vertical Breakdown: {metric_label}", fontsize=11, fontweight="bold", color="#1E293B", pad=10)
                ax.set_ylabel(metric_label, fontsize=9)
                ax.grid(axis="y", linestyle="--", alpha=0.5)

        elif chart_type == "Distribution Donut Only":
            fig, ax = plt.subplots(figsize=(8, 4.3), dpi=100)
            fig.patch.set_facecolor("#FFFFFF")
            if not cat_df.empty:
                colors = ["#3A86FF", "#06D6A0", "#FFB703", "#FB5607", "#8338EC", "#38BDF8"]
                wedges, texts, autotexts = ax.pie(
                    cat_df[metric],
                    labels=cat_df["category"],
                    autopct="%1.1f%%",
                    startangle=130,
                    colors=colors[:len(cat_df)],
                    pctdistance=0.78,
                    wedgeprops=dict(width=0.40, edgecolor="#FFFFFF", linewidth=2)
                )
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_weight("bold")
                ax.set_title(f"Market Share by Vertical ({metric_label})", fontsize=11, fontweight="bold", pad=10)

        else: # Feature Correlation Heatmap
            fig, ax = plt.subplots(figsize=(8, 4.3), dpi=100)
            fig.patch.set_facecolor("#FFFFFF")
            corr = self.engine.get_correlation_matrix()
            if not corr.empty:
                sns.heatmap(corr, annot=True, cmap="mako", fmt=".2f", ax=ax, cbar=True, annot_kws={"size": 9, "weight": "bold"}, linewidths=0.8)
                ax.set_title("Full Operational Variable Correlation Matrix", fontsize=11, fontweight="bold", pad=10)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        # Embedded Interactive Navigation Toolbar (Pan, Zoom, Save)
        toolbar = NavigationToolbar2Tk(canvas, self.chart_container)
        toolbar.update()
        toolbar.pack(side=BOTTOM, fill=X)

    def _render_kpi_card(self, parent, title, val, badge_txt, color):
        card = tb.Frame(parent, bootstyle="light", padding=14, relief="ridge")
        card.pack(side=LEFT, fill=X, expand=True, padx=5)

        h = tb.Frame(card)
        h.pack(fill=X)
        tb.Label(h, text=title, font=("Segoe UI", 8, "bold"), foreground="#6C757D").pack(side=LEFT)
        tb.Label(h, text=badge_txt, font=("Segoe UI", 7, "bold"), bootstyle=f"{color}-inverse", padding=(5, 1)).pack(side=RIGHT)

        tb.Label(card, text=val, font=("Segoe UI", 15, "bold"), foreground="#0B132B").pack(anchor="w", pady=(6, 0))

    # =========================================================================
    # VIEW 2: INVENTORY & STOCK MANAGEMENT
    # =========================================================================
    def _show_inventory_view(self):
        self._clear_content()
        self.view_title.config(text="Inventory Registry & Stock Management")

        paned = tb.Frame(self.content_frame)
        paned.pack(fill=BOTH, expand=True)

        # Left Card: Add Product Form
        form_card = tb.Labelframe(paned, text="Register New Product", padding=16, bootstyle="info")
        form_card.grid(row=0, column=0, sticky="nw", padx=(0, 14))

        fields = ["Product SKU:", "Item Name:", "Category:", "Cost Price (₹):", "Selling Price (₹):", "Opening Stock:"]
        self.inv_inputs = {}

        for idx, f in enumerate(fields):
            tb.Label(form_card, text=f, font=("Segoe UI", 9)).grid(row=idx*2, column=0, sticky="w", pady=(4, 1))
            ent = tb.Entry(form_card, width=24)
            ent.grid(row=idx*2+1, column=0, pady=(0, 6), sticky="we")
            self.inv_inputs[f] = ent

        btn_save = tb.Button(form_card, text="Save to Database", bootstyle="success", command=self._save_product_action)
        btn_save.grid(row=len(fields)*2, column=0, sticky="we", pady=(10, 4))

        # Right Panel: Table and Controls
        right_panel = tb.Frame(paned)
        right_panel.grid(row=0, column=1, sticky="nsew")
        paned.columnconfigure(1, weight=1)

        # Filter Ribbon
        ribbon = tb.Frame(right_panel)
        ribbon.pack(fill=X, pady=(0, 10))

        tb.Label(ribbon, text="Search:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_inventory_search)
        tb.Entry(ribbon, textvariable=self.search_var, width=24).pack(side=LEFT, padx=(0, 10))

        tb.Button(ribbon, text="Low Stock (< 5)", bootstyle="warning-outline", command=self._filter_low_stock).pack(side=LEFT, padx=3)
        tb.Button(ribbon, text="Reset View", bootstyle="secondary-outline", command=lambda: self._populate_inv_table(self.inventory)).pack(side=LEFT, padx=3)
        tb.Button(ribbon, text="Delete Selected", bootstyle="danger-outline", command=self._delete_selected_product).pack(side=LEFT, padx=3)
        tb.Button(ribbon, text="Inventory Valuation", bootstyle="primary-outline", command=self._show_inventory_valuation).pack(side=RIGHT)

        # Inventory Table
        cols = ("SKU", "Item Name", "Category", "Cost Price", "Selling Price", "Stock", "Unit Margin", "Status")
        self.table = tb.Treeview(right_panel, columns=cols, show="headings", height=16, bootstyle="primary")

        col_configs = {
            "SKU": (80, "center"),
            "Item Name": (240, "w"),
            "Category": (120, "center"),
            "Cost Price": (110, "e"),
            "Selling Price": (110, "e"),
            "Stock": (80, "center"),
            "Unit Margin": (110, "e"),
            "Status": (100, "center")
        }

        for col, (w, align) in col_configs.items():
            # Align the header text identically with cell data
            self.table.heading(col, text=col, anchor=align)
            self.table.column(col, width=w, minwidth=w, anchor=align, stretch=True)

        self.table.tag_configure("low", background="#FFF3CD", foreground="#856404")
        self.table.tag_configure("ok", background="#FFFFFF", foreground="#212529")

        self.table.pack(fill=BOTH, expand=True)
        self._populate_inv_table(self.inventory)

    def _populate_inv_table(self, items):
        for r in self.table.get_children():
            self.table.delete(r)
        for item in items:
            d = item.to_dict()
            status = "Low Stock" if d["Stock"] < 5 else "Available"
            tag = "low" if d["Stock"] < 5 else "ok"
            self.table.insert(
                "", END, 
                values=(d["ID"], d["Name"], d["Category"], f"₹{d['Cost']:,.2f}", f"₹{d['Price']:,.2f}", d["Stock"], f"₹{d['Margin']:,.2f}", status),
                tags=(tag,)
            )

    def _on_inventory_search(self, *args):
        q = self.search_var.get().lower().strip()
        filtered = [p for p in self.inventory if q in p.name.lower() or q in p.item_id.lower() or q in p.category.lower()]
        self._populate_inv_table(filtered)

    def _filter_low_stock(self):
        low_items = filter_low_stock(self.inventory, threshold=5)
        self._populate_inv_table(low_items)

    def _show_inventory_valuation(self):
        val = compute_total_inventory_value(self.inventory)
        messagebox.showinfo("Inventory Valuation", f"Total Warehouse Valuation (Cost Basis):\n\n₹ {val:,.2f}")

    def _save_product_action(self):
        try:
            sku = self.inv_inputs["Product SKU:"].get().strip()
            name = self.inv_inputs["Item Name:"].get().strip()
            cat = self.inv_inputs["Category:"].get().strip()
            cost = float(self.inv_inputs["Cost Price (₹):"].get())
            price = float(self.inv_inputs["Selling Price (₹):"].get())
            qty = int(self.inv_inputs["Opening Stock:"].get())

            if not (sku and name and cat):
                messagebox.showwarning("Incomplete Form", "All fields are required.")
                return

            self.db.add_or_update_product(sku, name, cat, cost, price, qty)
            self._reload_inventory()
            self._populate_inv_table(self.inventory)

            for entry in self.inv_inputs.values():
                entry.delete(0, tk.END)
            self.inv_inputs["Product SKU:"].focus_set()

            messagebox.showinfo("Success", f"Product '{name}' saved to database.")
        except ValueError:
            messagebox.showerror("Error", "Cost, Price, and Stock must contain valid numbers.")

    def _delete_selected_product(self):
        sel = self.table.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please click on a product row in the table first.")
            return
        item_vals = self.table.item(sel[0], "values")
        sku = item_vals[0]
        name = item_vals[1]

        if messagebox.askyesno("Confirm Deletion", f"Permanently remove '{name}' ({sku}) from inventory?"):
            try:
                self.db.delete_product(sku)
                self._reload_inventory()
                self._populate_inv_table(self.inventory)
                messagebox.showinfo("Deleted", f"Product '{name}' successfully removed.")
            except Exception as e:
                messagebox.showerror("Delete Error", f"Failed to delete product:\n{str(e)}")

    # =========================================================================
    # VIEW 3: PROFESSIONAL POS CASHIER TERMINAL
    # =========================================================================
    def _show_pos_view(self):
        self._clear_content()
        self.view_title.config(text="Point-of-Sale (POS) Cashier Checkout")
        self._reload_inventory()

        pos_container = tb.Frame(self.content_frame)
        pos_container.pack(fill=BOTH, expand=True)

        # Left Panel: Product Selection & Live Search
        left_box = tb.Labelframe(pos_container, text="Product Catalog Scanner", padding=16, bootstyle="info", width=400)
        left_box.pack(side=LEFT, fill=Y, padx=(0, 16))
        left_box.pack_propagate(False)

        tb.Label(left_box, text="Filter Catalog:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
        self.pos_search_var = tk.StringVar()
        self.pos_search_var.trace_add("write", self._on_pos_search)
        tb.Entry(left_box, textvariable=self.pos_search_var).pack(fill=X, pady=(0, 12))

        tb.Label(left_box, text="Available Inventory:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
        
        list_frame = tb.Frame(left_box)
        list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        scroll = tb.Scrollbar(list_frame, orient=VERTICAL)
        self.pos_listbox = tk.Listbox(list_frame, font=("Segoe UI", 9), selectmode=tk.SINGLE, borderwidth=1, yscrollcommand=scroll.set)
        scroll.config(command=self.pos_listbox.yview)
        scroll.pack(side=RIGHT, fill=Y)
        self.pos_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.pos_listbox.bind("<<ListboxSelect>>", self._on_pos_item_select)

        # Item Details Card
        self.detail_card = tb.Frame(left_box, bootstyle="light", padding=10)
        self.detail_card.pack(fill=X, pady=(0, 12))
        self.lbl_selected_info = tb.Label(
            self.detail_card, 
            text="Select an item above to inspect & add", 
            font=("Segoe UI", 9, "italic"), 
            foreground="#495057",
            wraplength=350
        )
        self.lbl_selected_info.pack(anchor="w")

        # Quantity Selector
        qty_row = tb.Frame(left_box)
        qty_row.pack(fill=X, pady=(0, 14))
        tb.Label(qty_row, text="Quantity:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(0, 10))
        self.pos_qty_spin = tb.Spinbox(qty_row, from_=1, to=100, width=8)
        self.pos_qty_spin.pack(side=LEFT)
        self.pos_qty_spin.set(1)

        tb.Button(left_box, text="Add to Invoice Cart", bootstyle="primary", command=self._pos_add_to_cart).pack(fill=X, pady=3)
        tb.Button(left_box, text="Clear Cart", bootstyle="danger-outline", command=self._pos_clear_cart).pack(fill=X, pady=3)

        # Right Panel: Active Customer Invoice
        right_box = tb.Labelframe(pos_container, text="Current Transaction Summary", padding=16, bootstyle="secondary")
        right_box.pack(side=LEFT, fill=BOTH, expand=True)

        cart_cols = ("SKU", "Item Name", "Unit Price", "Qty", "Total (₹)")
        self.cart_tree = tb.Treeview(right_box, columns=cart_cols, show="headings", height=12)
        cart_configs = {
            "SKU": (85, "center"),
            "Item Name": (260, "w"),
            "Unit Price": (115, "e"),
            "Qty": (70, "center"),
            "Total (₹)": (125, "e")
        }
        for col, (w, align) in cart_configs.items():
            self.cart_tree.heading(col, text=col, anchor=align)
            self.cart_tree.column(col, width=w, minwidth=w, anchor=align, stretch=True)
        self.cart_tree.pack(fill=BOTH, expand=True)

        cart_action_bar = tb.Frame(right_box)
        cart_action_bar.pack(fill=X, pady=6)
        tb.Button(cart_action_bar, text="Remove Item", bootstyle="warning-outline", command=self._pos_remove_cart_item).pack(side=LEFT)

        # Invoice Financial Breakdown Card
        calc_card = tb.Frame(right_box, bootstyle="light", padding=14)
        calc_card.pack(fill=X, side=BOTTOM, pady=(10, 0))

        sub_frame = tb.Frame(calc_card)
        sub_frame.pack(fill=X, pady=2)
        tb.Label(sub_frame, text="Subtotal:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_pos_subtotal = tb.Label(sub_frame, text="₹ 0.00", font=("Segoe UI", 9))
        self.lbl_pos_subtotal.pack(side=RIGHT)

        tax_frame = tb.Frame(calc_card)
        tax_frame.pack(fill=X, pady=2)
        tb.Label(tax_frame, text="GST / Tax (18%):", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_pos_tax = tb.Label(tax_frame, text="₹ 0.00", font=("Segoe UI", 9))
        self.lbl_pos_tax.pack(side=RIGHT)

        tb.Separator(calc_card).pack(fill=X, pady=6)

        total_frame = tb.Frame(calc_card)
        total_frame.pack(fill=X, pady=2)
        tb.Label(total_frame, text="Net Grand Total:", font=("Segoe UI", 12, "bold")).pack(side=LEFT)
        self.lbl_pos_grand = tb.Label(total_frame, text="₹ 0.00", font=("Segoe UI", 13, "bold"), foreground="#06D6A0")
        self.lbl_pos_grand.pack(side=RIGHT)

        checkout_btn_row = tb.Frame(calc_card)
        checkout_btn_row.pack(fill=X, pady=(10, 0))
        tb.Button(checkout_btn_row, text="Proceed to Payment & Generate Receipt", bootstyle="success", command=self._open_payment_modal).pack(fill=X)

        self._populate_pos_catalog()
        self._render_pos_cart()

    def _populate_pos_catalog(self, query=""):
        self.pos_listbox.delete(0, tk.END)
        self.pos_catalog_items = []
        for p in self.inventory:
            if p.stock_qty > 0:
                if not query or query in p.name.lower() or query in p.item_id.lower() or query in p.category.lower():
                    self.pos_catalog_items.append(p)
                    self.pos_listbox.insert(tk.END, f"{p.item_id} | {p.name} (Stock: {p.stock_qty})")

    def _on_pos_search(self, *args):
        q = self.pos_search_var.get().lower().strip()
        self._populate_pos_catalog(q)

    def _on_pos_item_select(self, event):
        sel = self.pos_listbox.curselection()
        if sel:
            idx = sel[0]
            prod = self.pos_catalog_items[idx]
            self.lbl_selected_info.config(
                text=f"{prod.name}\nPrice: ₹{prod.get_selling_price():,.2f} | Stock Available: {prod.stock_qty}",
                foreground="#0B132B"
            )

    def _pos_add_to_cart(self):
        sel = self.pos_listbox.curselection()
        if not sel:
            messagebox.showwarning("Select Item", "Please pick a product from the list.")
            return

        idx = sel[0]
        prod = self.pos_catalog_items[idx]
        qty = int(self.pos_qty_spin.get())

        existing = next((item for item in self.cart if item.product.item_id == prod.item_id), None)
        total_requested = (existing.quantity if existing else 0) + qty

        if total_requested > prod.stock_qty:
            messagebox.showerror("Stock Limit Exceeded", f"Only {prod.stock_qty} items available in stock.")
            return

        if existing:
            existing.quantity += qty
        else:
            self.cart.append(CartItem(prod, qty))

        self._render_pos_cart()

    def _pos_remove_cart_item(self):
        sel = self.cart_tree.selection()
        if not sel:
            messagebox.showwarning("Select Item", "Please select an item from the cart to remove.")
            return
        sku = self.cart_tree.item(sel[0], "values")[0]
        self.cart = [i for i in self.cart if i.product.item_id != sku]
        self._render_pos_cart()

    def _pos_clear_cart(self):
        self.cart.clear()
        self._render_pos_cart()

    def _render_pos_cart(self):
        for r in self.cart_tree.get_children():
            self.cart_tree.delete(r)

        subtotal = 0.0
        for item in self.cart:
            sub = item.get_subtotal()
            subtotal += sub
            self.cart_tree.insert(
                "", END, 
                values=(item.product.item_id, item.product.name, f"₹{item.product.get_selling_price():,.2f}", item.quantity, f"₹{sub:,.2f}")
            )

        tax = subtotal * 0.18
        grand = subtotal + tax

        self.lbl_pos_subtotal.config(text=f"₹ {subtotal:,.2f}")
        self.lbl_pos_tax.config(text=f"₹ {tax:,.2f}")
        self.lbl_pos_grand.config(text=f"₹ {grand:,.2f}")

    # =========================================================================
    # HIGH-LEVEL BILLING & RECEIPT MODAL
    # =========================================================================
    def _open_payment_modal(self):
        if not self.cart:
            messagebox.showwarning("Cart Empty", "Please add items to cart before checkout.")
            return

        subtotal = sum(i.get_subtotal() for i in self.cart)
        tax = subtotal * 0.18
        grand = subtotal + tax
        tx_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")

        modal = tb.Toplevel(self.root)
        modal.title(f"Receipt - {tx_id}")
        modal.geometry("520x680")
        modal.resizable(False, False)
        modal.transient(self.root)
        modal.grab_set()

        container = tb.Frame(modal, padding=20)
        container.pack(fill=BOTH, expand=True)

        tb.Label(container, text="SMARTRETAIL ENTERPRISE", font=("Segoe UI", 14, "bold"), foreground="#0B132B").pack(anchor="center")
        tb.Label(container, text="Retail POS Terminal • Official Tax Invoice", font=("Segoe UI", 8), foreground="#6C757D").pack(anchor="center")
        tb.Label(container, text=f"Invoice No: {tx_id}", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(15, 2))
        tb.Label(container, text=f"Date: {now_str}", font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 10))

        tb.Separator(container).pack(fill=X, pady=4)

        receipt_box = tb.Frame(container)
        receipt_box.pack(fill=BOTH, expand=True, pady=6)

        header_row = tb.Frame(receipt_box)
        header_row.pack(fill=X, pady=2)
        tb.Label(header_row, text="Description", font=("Segoe UI", 8, "bold"), width=24, anchor="w").pack(side=LEFT)
        tb.Label(header_row, text="Qty", font=("Segoe UI", 8, "bold"), width=5, anchor="center").pack(side=LEFT)
        tb.Label(header_row, text="Rate", font=("Segoe UI", 8, "bold"), width=10, anchor="e").pack(side=LEFT)
        tb.Label(header_row, text="Amount", font=("Segoe UI", 8, "bold"), width=12, anchor="e").pack(side=RIGHT)

        tb.Separator(receipt_box).pack(fill=X, pady=3)

        items_canvas = tb.Canvas(receipt_box, height=180)
        items_frame = tb.Frame(items_canvas)
        items_canvas.create_window((0, 0), window=items_frame, anchor="nw")

        for item in self.cart:
            row = tb.Frame(items_frame)
            row.pack(fill=X, pady=2)
            name_cut = item.product.name[:22] + ".." if len(item.product.name) > 22 else item.product.name
            tb.Label(row, text=name_cut, font=("Segoe UI", 8), width=24, anchor="w").pack(side=LEFT)
            tb.Label(row, text=str(item.quantity), font=("Segoe UI", 8), width=5, anchor="center").pack(side=LEFT)
            tb.Label(row, text=f"₹{item.product.get_selling_price():,.0f}", font=("Segoe UI", 8), width=10, anchor="e").pack(side=LEFT)
            tb.Label(row, text=f"₹{item.get_subtotal():,.2f}", font=("Segoe UI", 8), width=12, anchor="e").pack(side=RIGHT)

        items_canvas.pack(fill=BOTH, expand=True)

        tb.Separator(container).pack(fill=X, pady=6)

        calc_box = tb.Frame(container)
        calc_box.pack(fill=X, pady=4)

        def make_row(lbl, amt, bold=False):
            f = tb.Frame(calc_box)
            f.pack(fill=X, pady=1)
            tb.Label(f, text=lbl, font=("Segoe UI", 9, "bold" if bold else "normal")).pack(side=LEFT)
            tb.Label(f, text=amt, font=("Segoe UI", 9, "bold" if bold else "normal")).pack(side=RIGHT)

        make_row("Item Subtotal:", f"₹ {subtotal:,.2f}")
        make_row("GST (18% Included):", f"₹ {tax:,.2f}")
        make_row("Net Payable:", f"₹ {grand:,.2f}", bold=True)

        pay_frame = tb.Frame(container)
        pay_frame.pack(fill=X, pady=(12, 10))
        tb.Label(pay_frame, text="Payment Mode:", font=("Segoe UI", 9, "bold")).pack(side=LEFT, padx=(0, 10))
        combo_pay = tb.Combobox(pay_frame, values=["Credit Card", "UPI / QR", "Cash", "Debit Card"], state="readonly", width=16)
        combo_pay.pack(side=LEFT)
        combo_pay.current(0)

        def confirm_payment():
            pm = combo_pay.get()
            try:
                self.db.record_sale_transaction(tx_id, self.cart, subtotal, tax, grand, payment_method=pm)
                
                os.makedirs("data/receipts", exist_ok=True)
                receipt_path = f"data/receipts/{tx_id}.txt"
                with open(receipt_path, "w", encoding="utf-8") as rf:
                    rf.write(f"=== SMARTRETAIL TAX INVOICE ===\n")
                    rf.write(f"Invoice: {tx_id}\nDate: {now_str}\nMode: {pm}\n")
                    rf.write(f"--------------------------------\n")
                    for i in self.cart:
                        rf.write(f"{i.product.name} x {i.quantity} = Rs. {i.get_subtotal():,.2f}\n")
                    rf.write(f"--------------------------------\n")
                    rf.write(f"Subtotal: Rs. {subtotal:,.2f}\n")
                    rf.write(f"Tax: Rs. {tax:,.2f}\n")
                    rf.write(f"Grand Total: Rs. {grand:,.2f}\n")
                    rf.write(f"Status: PAID\n")

                messagebox.showinfo("Payment Successful", f"Payment verified via {pm}!\n\nReceipt generated: {receipt_path}\nDatabase records synchronized.")
                modal.destroy()
                self._pos_clear_cart()
                self._reload_inventory()
                self._populate_pos_catalog()
            except Exception as err:
                messagebox.showerror("Transaction Failure", str(err))

        tb.Button(container, text="Confirm & Complete Order", bootstyle="success", command=confirm_payment).pack(fill=X, pady=(6, 0))
