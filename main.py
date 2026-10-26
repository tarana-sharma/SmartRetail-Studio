"""
SmartRetail Studio Pro - Master Application Entry Point
"""
import ttkbootstrap as tb
from gui.dashboard_gui import SmartRetailEnterpriseApp

def main():
    root = tb.Window(themename="flatly")
    app = SmartRetailEnterpriseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
