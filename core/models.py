"""
Core Domain Models for Retail Products and Transactions.
"""

class Item:
    """Base item model."""
    def __init__(self, item_id: str, name: str, category: str):
        self.item_id = item_id
        self.name = name
        self.category = category

    def __str__(self) -> str:
        return f"[{self.item_id}] {self.name} ({self.category})"


class RetailProduct(Item):
    """Encapsulated product entity with pricing and stock tracking."""
    def __init__(self, item_id: str, name: str, category: str, cost_price: float, selling_price: float, stock_qty: int):
        super().__init__(item_id, name, category)
        self.__cost_price = float(cost_price)
        self.__selling_price = float(selling_price)
        self.stock_qty = int(stock_qty)

    def get_cost_price(self) -> float:
        return self.__cost_price

    def get_selling_price(self) -> float:
        return self.__selling_price

    def set_selling_price(self, new_price: float) -> None:
        if new_price > 0:
            self.__selling_price = float(new_price)
        else:
            raise ValueError("Selling price must be greater than zero.")

    def get_margin(self) -> float:
        """Returns unit gross profit margin."""
        return round(self.__selling_price - self.__cost_price, 2)

    def reduce_stock(self, quantity: int) -> bool:
        if 0 < quantity <= self.stock_qty:
            self.stock_qty -= quantity
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "ID": self.item_id,
            "Name": self.name,
            "Category": self.category,
            "Cost": self.__cost_price,
            "Price": self.__selling_price,
            "Stock": self.stock_qty,
            "Margin": self.get_margin()
        }


class CartItem:
    """Represents a billed transaction item."""
    def __init__(self, product: RetailProduct, quantity: int):
        self.product = product
        self.quantity = int(quantity)

    def get_subtotal(self) -> float:
        return round(self.product.get_selling_price() * self.quantity, 2)
