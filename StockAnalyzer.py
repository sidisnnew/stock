import tkinter as tk
from tkinter import ttk, messagebox

import yfinance as yf
import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from analysis import forecast_next_close

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

        # Summary
        summaryFrame = ttk.LabelFrame(self.mw, text="Summary", padding=10)
        summaryFrame.pack(fill="x", padx=12, pady=(0, 8))
        self.summary = tk.StringVar(value="Latest close: --   Daily change: --   20-day MA: --   50-day MA: --")
        ttk.Label(summaryFrame, textvariable=self.summary).pack(anchor="w")

        # Forecast (Just for fun)
        self.forecast = tk.StringVar(value="At least 6 months")
        forecastFrame = ttk.LabelFrame(self.mw, text="Estimate for the next trading day", padding=10)
        forecastFrame.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Label(forecastFrame, textvariable=self.forecast, wraplength=1400).pack(anchor="w")

        # Information
        infoFrame = ttk.LabelFrame(self.mw, text="Information")
        infoFrame.pack(fill="x", padx=12, pady=(0, 8))
        self.info = {}
        infoItem = [
            ("P/E", "pe"),
            ("EPS", "eps"),
            ("Revenue", "revenue"),
            ("Revenue growth", "revenue_growth"),
            ("Net income growth", "income_growth"),
            ("Free cash flow", "free_cash_flow"),
            ("Total debt", "total_debt"),
            ("Dividend yield", "dividend_yield")
        ]
        for index, (label, key) in enumerate(infoItem):
            row = index // 2
            col = index % 2 * 2
            value = tk.StringVar(value="--")
            self.info[key] = value
            ttk.Label(infoFrame, text=f"{label}: ").grid(row=row, column=col, padx=(10, 5), pady=(5, 5), sticky="w")
            ttk.Label(infoFrame, textvariable=value, width=20).grid(row=row, column=col+1, pady=(5, 5))

        # Valuation
        valFrame = ttk.LabelFrame(self.mw, text="Valuation")
        valFrame.pack(fill="x", padx=12, pady=(0, 8))
        self.val = {}
        valItem = [
            ("Forward P/E", "forward_pe"),
            ("PEG ratio", "peg"),
            ("Price-to-Book (P/B)", "price_to_book"),
            ("Price-to-Sales (P/S)", "price_to_sales"),
            ("Estimated fair value", "fair_value"),
            ("Difference vs. latest close", "difference")
        ]
        for index, (label, key) in enumerate(valItem):
            row = index // 2
            col = index % 2 * 2
            value = tk.StringVar(value="--")
            self.val[key] = value
            ttk.Label(valFrame, text=f"{label}:").grid(row=row, column=col, padx=(10, 5), pady=(5, 5), sticky="w")
            ttk.Label(valFrame, textvariable=value, width=20).grid(row=row, column=col+1, pady=(5, 5))

        # Score
        scoreFrame = ttk.LabelFrame(self.mw, text="Score")
        scoreFrame.pack(fill="x", padx=12, pady=(0,8))
        self.score = tk.StringVar(value="--")
        self.level = tk.StringVar(value="--")
        ttk.Label(scoreFrame, text="Score: ").grid(row=0, column=0, padx=(10, 5), pady=(5, 5), sticky="w")
        ttk.Label(scoreFrame, textvariable=self.score).grid(row=0, column=1, pady=(5, 5))
        ttk.Label(scoreFrame, text="Risky Level: ").grid(row=1, column=0, padx=(10, 5), pady=(5, 5), sticky="w")
        ttk.Label(scoreFrame, textvariable=self.level).grid(row=1, column=1, pady=(5, 5))

        # Chart
        self.figure = Figure(figsize=(16, 9), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title("Stock Price")
        self.axes.set_xlabel("Date")
        self.axes.set_ylabel("Price")
        self.axes.grid(True, alpha=0.2)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.mw)
        self.canvas.get_tk_widget().pack(fill="x", expand=True, padx=10, pady=(0,15))
        self.canvas.draw()

    # action after press search
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
                dailyChangeText = "Not enough data (At least 6 months)"
            # Forecast
            if period not in ("1d", "5d", "1mo", "3mo"):
                self.showForecast(dailyData)
            else:
                self.forecast.set("Not enough data (Need at least 60 records)")

            # Summary
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

            # Load information
            self.loadInfo(stock)

            # Load valuation
            self.loadVal(stock, latestClose)
            
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

    # handle information
    def loadInfo(self, stock):
        # initialize
        for value in self.info.values():
            value.set("--")
        infoTemp = {}
        try:
            infoTemp = stock.info
        except Exception as error:
            messagebox.showerror("Error", error)

        pe = infoTemp.get("trailingPE")
        eps = infoTemp.get("trailingEps")
        revenue = infoTemp.get("totalRevenue")
        freeCashflow = infoTemp.get("freeCashflow")
        totalDebt = infoTemp.get("totalDebt")
        dividendYield = infoTemp.get("dividendYield")

        def checkContent(content):
            try:
                if content is None:
                    return "n/a"
                return f"{float(content):,.2f}"
            except:
                return "n/a"

        self.info["pe"].set(checkContent(pe))
        self.info["eps"].set(f"${checkContent(eps)}")
        self.info["revenue"].set(f"${checkContent(revenue)}")
        self.info["free_cash_flow"].set(f"${checkContent(freeCashflow)}")
        self.info["total_debt"].set(f"${checkContent(totalDebt)}")
        if checkContent(dividendYield) != "n/a":
            self.info["dividend_yield"].set(f"{checkContent(dividendYield)}%")
        else:
            self.info["dividend_yield"].set(f"{checkContent(dividendYield)}")
        self.info["total_debt"].set(f"${checkContent(totalDebt)}")

        try:
            financial = stock.financials
        except Exception as error:
            messagebox.showerror("Error", error)

        if not financial.empty and len(financial.columns)>=2:
            if "Operating Revenue" in financial.index:
                revenue = financial.loc["Operating Revenue"]
            elif "Total Revenue" in financial.index:
                revenue = financial.loc["Total Revenue"]
            else:
                revenue = None

            if "Net Income" in financial.index:
                income = financial.loc["Net Income"]
            else:
                income = None

        if not revenue.empty:
            self.info["revenue_growth"].set(f"{(revenue.iloc[0]-revenue.iloc[1])/revenue.iloc[1]*100:+,.2f}%")
        else:
            self.info["revenue_growth"].set("n/a")

        if not income.empty:
            self.info["income_growth"].set(f"{(income.iloc[0]-income.iloc[1])/income.iloc[1]*100:+,.2f}%")    
        else:
            self.info["income_growth"].set("n/a") 

        self.calScore(infoTemp)

    # handle valuation
    def loadVal(self, stock, latestClose):
        try:
            info = stock.info
        except Exception as error:
            messagebox.showerror("Error", error)

        def checkContent(content):
            try:
                if content is None:
                    return "n/a"
                return f"{float(content):,.2f}"
            except:
                return "n/a"
        try:
            fairValue = float(checkContent(info.get("forwardPE"))) * float(checkContent(info.get("trailingEps")))
            differencePct = (fairValue - latestClose) / latestClose *100
        except:
            fairValue = "n/a"
            differencePct = "n/a"

        self.val["forward_pe"].set(checkContent(info.get("forwardPE")))
        self.val["peg"].set(checkContent(info.get("pegRatio")))
        self.val["price_to_book"].set(checkContent(info.get("priceToBook")))
        self.val["price_to_sales"].set(checkContent(info.get("priceToSalesTrailing12Months")))
        self.val["fair_value"].set(f"${checkContent(fairValue)}")
        self.val["difference"].set(f"{checkContent(differencePct)}%")

    def calScore(self, info):
        score = 0
        max = 0
        
        pe = info.get("trailingPE")
        if pe is not None and pe > 0:
            max += 25
            if pe <= 10:
                score += 25
            elif pe <=20:
                score += 18.5
            elif pe <= 30:
                score += 12
            else:
                score += 5

        eps = info.get("trailingEps")
        if eps is not None:
            max += 25
            if eps >= 10:
                score +=25
            elif eps >= 5:
                score += 15
            elif eps > 0:
                score += 5

        if max != 0:
            self.score.set(value= f"{score/max:.1f}")
            if score/max >= 0.7:
                self.level.set("Low")
            elif score/max >=0.4:
                self.level.set("Medium")
            else:
                self.level.set("High")
        else:
            self.score.set("n/a")
            self.level.set("n/a")

    def showForecast(self, dailyData):
        try:
            result = forecast_next_close(dailyData)
            self.forecast.set(
                f"Estimate the closing price for the next trading day: ${result.predicted_close:.2f}   "
                f"Test MAE: ${result.mae:.2f}   Test RMSE: ${result.rmse:.2f}   "
                f"Simple MAE: ${result.baseline_mae:.2f}"
            )
        except ValueError as error:
            self.forecast.set(f"Error: {error}")

        
if __name__ == "__main__":
    mw = tk.Tk()
    analyzer = StockAnalyzer(mw)
    mw.mainloop()