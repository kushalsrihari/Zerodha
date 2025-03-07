import tkinter as tk
from tkinter import messagebox
from fyers_apiv3 import fyersModel
import webbrowser

# API credentials
APP_ID = "RX6DYO4KLQ-100"
SECRET_ID = "N23FCL8SAZ"
REDIRECT_URI = "https://www.example.com"  # Replace with your actual redirect URI if set in Fyers app settings

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fyers Algo Trading App")
        
        # Login section
        tk.Label(root, text="Fyers Login").pack()
        tk.Button(root, text="Log in to Fyers", command=self.login).pack()
        self.auth_code_entry = tk.Entry(root)
        self.auth_code_entry.pack()
        tk.Button(root, text="Submit Auth Code", command=self.submit_auth_code).pack()
        
        # Trading inputs
        tk.Label(root, text="Total Investment Amount (INR)").pack()
        self.investment_entry = tk.Entry(root)
        self.investment_entry.pack()
        
        tk.Label(root, text="Stocks (comma-separated, e.g., NSE:INFY-EQ,NSE:RELIANCE-EQ)").pack()
        self.stocks_entry = tk.Entry(root)
        self.stocks_entry.pack()
        
        tk.Label(root, text="Target Percentage (%)").pack()
        self.target_entry = tk.Entry(root)
        self.target_entry.pack()
        
        tk.Label(root, text="Stop-Loss Percentage (%)").pack()
        self.stop_loss_entry = tk.Entry(root)
        self.stop_loss_entry.pack()
        
        self.action_var = tk.StringVar(value="buy")
        tk.Radiobutton(root, text="Buy", variable=self.action_var, value="buy").pack()
        tk.Radiobutton(root, text="Sell", variable=self.action_var, value="sell").pack()
        
        tk.Button(root, text="Place Orders", command=self.place_orders).pack()
        
        self.fyers = None
    
    def login(self):
        """Generate authentication URL and open it in the browser."""
        session = fyersModel.SessionModel(
            client_id=APP_ID,
            secret_key=SECRET_ID,
            redirect_uri=REDIRECT_URI,
            response_type="code",
            grant_type="authorization_code"
        )
        auth_url = session.generate_authcode()
        webbrowser.open(auth_url)
    
    def submit_auth_code(self):
        """Submit the authorization code to obtain access token."""
        auth_code = self.auth_code_entry.get()
        if not auth_code:
            messagebox.showerror("Error", "Please enter the authorization code")
            return
        session = fyersModel.SessionModel(
            client_id=APP_ID,
            secret_key=SECRET_ID,
            redirect_uri=REDIRECT_URI,
            response_type="code",
            grant_type="authorization_code"
        )
        session.set_token(auth_code)
        try:
            response = session.generate_token()
            access_token = response["access_token"]
            self.fyers = fyersModel.FyersModel(client_id=APP_ID, token=access_token, log_path="/logs")
            messagebox.showinfo("Success", "Logged in successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")
    
    def place_orders(self):
        """Process inputs and place bracket orders."""
        if not self.fyers:
            messagebox.showerror("Error", "Please log in first")
            return
        
        try:
            total_investment = float(self.investment_entry.get())
            stocks = [s.strip() for s in self.stocks_entry.get().split(",")]
            target_percentage = float(self.target_entry.get())
            stop_loss_percentage = float(self.stop_loss_entry.get())
            action = self.action_var.get()
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please enter numeric values where required.")
            return
        
        if not stocks:
            messagebox.showerror("Error", "Please enter at least one stock")
            return
        
        amount_per_stock = total_investment / len(stocks)
        
        for stock in stocks:
            # Fetch current price
            quote_response = self.fyers.quotes({"symbols": stock})
            if quote_response["s"] != "ok" or not quote_response["d"]:
                messagebox.showerror("Error", f"Failed to get quote for {stock}")
                continue
            current_price = quote_response["d"][0]["v"]["lp"]
            
            # Calculate quantity
            quantity = int(amount_per_stock / current_price)
            if quantity == 0:
                messagebox.showwarning("Warning", f"Insufficient amount for {stock}. Skipping.")
                continue
            
            # Calculate stop-loss and target prices
            if action == "buy":
                stop_loss_price = round(current_price * (1 - stop_loss_percentage / 100), 2)
                target_price = round(current_price * (1 + target_percentage / 100), 2)
                side = 1  # Buy
            else:  # sell (assuming short selling for bracket order)
                stop_loss_price = round(current_price * (1 + stop_loss_percentage / 100), 2)
                target_price = round(current_price * (1 - target_percentage / 100), 2)
                side = -1  # Sell
            
            # Define bracket order parameters
            order_data = {
                "symbol": stock,
                "qty": quantity,
                "type": 2,  # Market order
                "side": side,
                "productType": "BO",
                "limitPrice": 0,
                "stopPrice": 0,
                "validity": "DAY",
                "stopLoss": abs(current_price - stop_loss_price),  # Difference in price
                "takeProfit": abs(target_price - current_price),   # Difference in price
                "offlineOrder": False
            }
            
            try:
                response = self.fyers.place_order(order_data)
                if response["s"] == "ok":
                    messagebox.showinfo("Success", f"Bracket order placed for {stock}")
                else:
                    messagebox.showerror("Error", f"Failed to place order for {stock}: {response['message']}")
            except Exception as e:
                messagebox.showerror("Error", f"Order placement failed for {stock}: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()
