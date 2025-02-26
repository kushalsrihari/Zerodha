import tkinter as tk
from tkinter import messagebox
from fyers_api import fyersModel, accessToken

class TradingApp:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Fyers Algorithmic Trader")

        # UI Elements
        tk.Label(self.window, text="Client ID:").grid(row=0, column=0, padx=10, pady=5)
        self.client_id_entry = tk.Entry(self.window)
        self.client_id_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Secret Key:").grid(row=1, column=0, padx=10, pady=5)
        self.secret_entry = tk.Entry(self.window, show="*")
        self.secret_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Auth PIN:").grid(row=2, column=0, padx=10, pady=5)
        self.pin_entry = tk.Entry(self.window)
        self.pin_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Investment (₹):").grid(row=3, column=0, padx=10, pady=5)
        self.investment_entry = tk.Entry(self.window)
        self.investment_entry.grid(row=3, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Stocks (comma-separated):").grid(row=4, column=0, padx=10, pady=5)
        self.stocks_entry = tk.Entry(self.window)
        self.stocks_entry.grid(row=4, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Target (%):").grid(row=5, column=0, padx=10, pady=5)
        self.target_entry = tk.Spinbox(self.window, from_=0.1, to=100, increment=0.1)
        self.target_entry.grid(row=5, column=1, padx=10, pady=5)

        tk.Label(self.window, text="Stop-loss (%):").grid(row=6, column=0, padx=10, pady=5)
        self.stoploss_entry = tk.Spinbox(self.window, from_=0.1, to=100, increment=0.1)
        self.stoploss_entry.grid(row=6, column=1, padx=10, pady=5)

        self.order_type = tk.StringVar(value="buy")
        tk.Radiobutton(self.window, text="Buy", variable=self.order_type, value="buy").grid(row=7, column=0)
        tk.Radiobutton(self.window, text="Sell", variable=self.order_type, value="sell").grid(row=7, column=1)

        tk.Button(self.window, text="Execute Orders", command=self.execute_orders).grid(row=8, column=0, columnspan=2, pady=10)

    def authenticate(self, client_id, secret, pin):
        session = accessToken.SessionModel(
            client_id=client_id,
            secret_key=secret,
            redirect_uri="https://www.google.com/",
            response_type="code",
            grant_type="authorization_code"
        )
        try:
            session.set_token(pin)
            token_data = session.generate_token()
            return token_data["access_token"]
        except Exception as e:
            messagebox.showerror("Authentication Failed", str(e))
            return None

    def get_ltp(self, fyers_client, symbol):
        try:
            response = fyers_client.quotes({"symbols": symbol})
            if response["code"] == 200:
                return response["data"][0]["ltp"]
            else:
                messagebox.showerror("Error", f"Failed to fetch LTP: {response['message']}")
                return None
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None

    def place_order(self, fyers_client, symbol, qty, side, ltp, target_percent, stoploss_percent):
        try:
            if side == "buy":
                target_price = round(ltp * (1 + target_percent / 100), 2)
                stoploss_price = round(ltp * (1 - stoploss_percent / 100), 2)
            else:
                target_price = round(ltp * (1 - target_percent / 100), 2)
                stoploss_price = round(ltp * (1 + stoploss_percent / 100), 2)

            order_params = {
                "symbol": symbol,
                "qty": int(qty),
                "type": 2,
                "side": 1 if side == "buy" else -1,
                "productType": "INTRADAY",
                "limitPrice": round(ltp, 2),
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": "False",
                "stopLoss": stoploss_price,
                "takeProfit": target_price
            }
            response = fyers_client.place_order(order_params)
            return response
        except Exception as e:
            messagebox.showerror("Order Error", str(e))
            return None

    def execute_orders(self):
        client_id = self.client_id_entry.get()
        secret = self.secret_entry.get()
        pin = self.pin_entry.get()
        investment = float(self.investment_entry.get())
        stocks = [s.strip() for s in self.stocks_entry.get().split(",")]
        target = float(self.target_entry.get())
        stoploss = float(self.stoploss_entry.get())
        side = self.order_type.get()

        access_token = self.authenticate(client_id, secret, pin)
        if not access_token:
            return

        fyers = fyersModel.FyersModel(client_id=client_id, token=access_token)
        allocation = investment / len(stocks) if len(stocks) > 0 else 0

        for symbol in stocks:
            ltp = self.get_ltp(fyers, symbol)
            if not ltp:
                continue
            qty = allocation // ltp
            if qty < 1:
                messagebox.showwarning("Skipped", f"Insufficient allocation for {symbol}")
                continue
            response = self.place_order(fyers, symbol, qty, side, ltp, target, stoploss)
            if response and response.get("code") == 200:
                messagebox.showinfo("Success", f"Order placed for {symbol}")
            else:
                messagebox.showerror("Failed", f"Order failed for {symbol}: {response.get('message')}")

if __name__ == "__main__":
    app = TradingApp()
    app.window.mainloop()
