import tkinter as tk
from soniclit.gui.desktop.app import SonicLitApp

def main():
    root = tk.Tk()
    app = SonicLitApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
