import tkinter as tk
from dhvani.gui.desktop.app import DhvaniApp

def main():
    root = tk.Tk()
    app = DhvaniApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
