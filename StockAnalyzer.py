import tkinter as tk
from tkinter import ttk, messagebox

import yfinance as yf
import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StockAnalyzer:
    def __init__(self, mw):
        self.mw = mw
        self.mw.title("US stock")
        self.mw.geometry("1920x1080")

        # Search attribute
        frame = ttk.Frame(self.mw, padding=12)
        frame.pack(fill="x")
        
        ttk.Label(frame, text="Stock: ").grid(row=0, column=0, padx=(0, 5), pady=5)
        self.tEntry = ttk.Entry(frame, width=10)
        self.tEntry.grid(row=0, column=1, padx=(0, 10), pady=4)
        
        ttk.Label(frame, text="Period: ").grid(row=0, column=2, padx=(0, 5), pady=5)
        self.pVar = tk.StringVar(value="1d")
        self.pBox = ttk.Combobox(frame, textvariable=self.pVar, values=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"], width=6, state="readonly")
        self.pBox.grid(row=0, column=3, padx=(0, 10), pady=5)
        
        self.sButton = ttk.Button(frame, text="Search", command=self.analyze)
        self.sButton.grid(row=0, column=4, padx=5, pady=5)

        # Summary display
        summaryFrame = ttk.LabelFrame(self.mw, text="Summary", padding=10)
        summaryFrame.pack(fill="x", padx=12, pady=(0, 8))
        self.summary = tk.StringVar(value="Latest close: --   Daily change: --   20-day MA: --   50-day MA: --")
        ttk.Label(summaryFrame, textvariable=self.summary).pack(anchor="w")

        # Chart
        self.figure = Figure(figsize=(10, 10), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title("Stock Price")
        self.axes.set_xlabel("Date")
        self.axes.set_ylabel("Price")
        self.axes.grid(True, alpha=0.2)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.mw)
        self.canvas.get_tk_widget().pack(fill="x", expand=True, padx=10, pady=(0,15))
        self.canvas.draw()

    def analyze(self):
        ticker = self.tEntry.get().strip().upper()
        period = self.pVar.get()
        if period == "1d" or period == "5d":
            interval = "1m"
        else:
            interval = "1d"
        if not ticker:
            messagebox.showwarning("Missing ticker", "Input please")
            return
        
        self.sButton.config(state="disabled")
        self.mw.update_idletasks()
        try:
            stock = yf.Ticker(ticker)
            dailyData = stock.history(period=period)
            data = stock.history(period=period, interval=interval)
            if data.empty:
                raise ValueError(
                    "No data was returned. Try again."
                )
            dailyData = dailyData.dropna(subset=["Close"])
            data = data.dropna(subset=["Close"])
            if data.empty:
                raise ValueError(
                    "No data was returned. Try again."
                )
            
            latestClose = float(data["Close"].iloc[-1])
            latestDate = data.index[-1].strftime("%Y-%m-%d")
            if len(dailyData) >=2:
                previousClose = float(dailyData["Close"].iloc[-2])
                dailyChange = latestClose - previousClose
                dcPercent = (dailyChange/previousClose) * 100
                dailyChangeText = f"{dailyChange:+.2f} ({dcPercent:+.2f}%)"
            else:
                dailyChangeText = "Not enough data"

            if period != "1d" and period != "5d":
                data["MA20"] = data["Close"].rolling(window=20).mean()
                data["MA50"] = data["Close"].rolling(window=50).mean()
                ma20 = data["MA20"].iloc[-1]
                ma50 = data["MA50"].iloc[-1]
                ma20Text = f"{ma20:.2f}" if pd.notna(ma20) else "Not enough data"
                ma50Text = f"{ma50:.2f}" if pd.notna(ma50) else "Not enough data"
            else:
                ma20Text = "Not enough data"
                ma50Text = "Not enough data"

            self.summary.set(f"{ticker} | Latest close({latestDate}): {latestClose:.2f}   Daily Change: {dailyChangeText}   MA20: {ma20Text}   MA50: {ma50Text}")
            
            # plot graph
            self.axes.clear()
            self.axes.plot(data.index, data["Close"], label="Closing price")
            if period != "1d" and period != "5d":
                self.axes.plot(data.index, data["MA20"], label="MA20")
                self.axes.plot(data.index, data["MA50"], label="MA50")
            self.axes.set_title(f"{ticker}")
            self.axes.set_xlabel("Date")
            self.axes.set_ylabel("Price")
            self.axes.grid(True, alpha=0.2)
            self.axes.legend()
            self.canvas.draw()
        except Exception as error:
            messagebox.showerror("Error", error)
        finally:
            self.sButton.config(state="normal")


if __name__ == "__main__":
    mw = tk.Tk()
    analyzer = StockAnalyzer(mw)
    mw.mainloop()