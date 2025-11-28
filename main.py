import os
from dotenv import load_dotenv
load_dotenv()
from ui.main_window import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
