"""
ui/splash.py — PlanHub v1.0
Écran de démarrage — utilise after() (thread-safe, pas de threading).
"""

import tkinter as tk


class SplashScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def show(self, duration: float = 2.5):
        """Affiche le splash screen animé pendant `duration` secondes."""
        splash = tk.Toplevel(self.root)
        splash.overrideredirect(True)
        splash.configure(bg="#FFFFFF")

        w, h = 520, 300
        sw = splash.winfo_screenwidth()
        sh = splash.winfo_screenheight()
        splash.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        splash.configure(highlightbackground="#E0E0E0", highlightthickness=1)

        canvas = tk.Canvas(splash, width=w, height=h, bg="#FFFFFF",
                            highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Logo
        canvas.create_oval(w//2 - 50, 50, w//2 + 50, 150,
                            fill="#1565C0", outline="")
        canvas.create_text(w//2, 100, text="PH",
                            font=("Segoe UI", 28, "bold"), fill="white")
        canvas.create_text(w//2, 175, text="PlanHub",
                            font=("Segoe UI", 24, "bold"), fill="#1565C0")
        canvas.create_text(w//2, 200, text="v1.0",
                            font=("Segoe UI", 11), fill="#616161")
        canvas.create_text(w//2, 225,
                            text="Du DQE à Primavera P6 en quelques clics",
                            font=("Segoe UI", 10, "italic"), fill="#42A5F5")

        bar_y = 260
        canvas.create_rectangle(60, bar_y, w - 60, bar_y + 8,
                                 fill="#E0E0E0", outline="")
        progress_bar = canvas.create_rectangle(60, bar_y, 60, bar_y + 8,
                                               fill="#1565C0", outline="")

        # Animation 100 % dans le thread principal via after()
        steps = 40
        bar_width = w - 120
        interval_ms = max(1, int(duration * 1000 / steps))

        def update_step(step):
            if step > steps:
                splash.destroy()
                self.root.destroy()
                return
            x2 = 60 + int(bar_width * step / steps)
            canvas.coords(progress_bar, 60, bar_y, x2, bar_y + 8)
            self.root.after(interval_ms, update_step, step + 1)

        self.root.after(0, update_step, 0)
        self.root.mainloop()
