import os
import json
import webbrowser
from tkinter import *
from tkinter import ttk, messagebox, simpledialog
from fyers_api import accessToken, fyersModel

# Load configuration
with open('config.json') as f:
    config = json.load(f)

client_id = config['client_id']
secret_key = config['secret_key']
redirect_uri = config['redirect_uri']

class TradingApp:
    def __init__(self, master):
        self.master = master
        master.title("Fyers Trading App")
        self.access_token = None
        self.fyers = None
        
        # Check for existing access token
        if os.path.exists('access_token.txt'):
            with open('access_token.txt', 'r') as f:
                self.access_token = f.read().strip()
            self.fyers = fyersModel.FyersModel(client_id=client_id, token=self.access_token)
        else:
            self.authenticate()
        
        # Initialize UI components
        self.setup_ui()
    
    def authenticate(self):
        session = accessToken.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            response_type='code',
            grant_type='authorization_code'
        )
        auth_url = session.generate_authcode()
        webbrowser.open(auth_url)
        auth_code = simpledialog.askstring("Auth Code", "Enter auth code from URL:")
        session.set_token(auth_code)
        response = session.generate_token()
        self.access_token = response['access_token']
        with open('access_token.txt', 'w') as f:
            f.write(self.access_token)
        self.fyers = fyersModel.FyersModel(client_id=client_id, token=self.access_token)
    
    def setup_ui(self):
        Label(self.master, text="Total Investment:").grid(row=0, column=0, padx=10, pady=5)
        self.total_investment = Entry(self.master)
        self.total_investment.grid(row=0, column=1, padx=10, pady=5)
        
        Label(self.master, text="Stocks (one per line):").grid(row=1, column=0, padx=10, pady=5)
        self.stocks = Text(self.master, height=5, width=30)
        self.stocks.grid(row=1, column=1, padx=10, pady=5)
        
        Label(self.master, text="Target %:").grid(row=2, column=0, padx=10, pady=5)
        self.target = Entry(self.master)
        self.target.grid(row=2, column=1, padx=10, pady=5)
        
        Label(self.master, text="Stop-Loss %:").grid(row=3, column=0, padx=10, pady=5)
        self.stoploss = Entry(self.master)
        self.stoploss.grid(row=3, column=1, padx=10, pady=5)
        
        Label(self.master, text="Action:").grid(row=4, column=0, padx=10, pady=5)
        self.action = ttk.Combobox(self.master, values=["Buy", "Sell"])
        self.action.grid(row=4, column=1, padx=10, pady=5)
        self.action.current(0)
        
        self.execute_btn = Button(self.master, text="Execute Orders", command=self.execute_orders)
        self.execute_btn.grid(row=5, column=0, columnspan=2, pady=10)
    
    def execute_orders(self):
        try:
            total = float(self.total_investment.get())
            stocks = self.stocks.get("1.0", END).strip().split('\n')
            target_pct = float(self.target.get()) / 100
            stoploss_pct = float(self.stoploss.get()) / 100
            action = self.action.get().lower()
            
            if not stocks:
                messagebox.showerror("Error", "Enter at least one stock symbol.")
                return
            
            per_stock = total / len(stocks)
            
            for symbol in stocks:
                symbol = symbol.strip()
                if not symbol:
                    continue
                
                # Fetch LTP
                quote = self.fyers.quotes({'symbols': symbol})
                if quote['code'] != 200:
                    messagebox.showerror("Error", f"Failed to fetch price for {symbol}")
                    continue
                ltp = quote['data'][0]['lp']
                
                quantity = int(per_stock / ltp)
                if quantity <= 0:
                    messagebox.showwarning("Warning", f"Skipping {symbol} (quantity zero)")
                    continue
                
                # Calculate target and stop-loss prices
                if action == 'buy':
                    target_price = ltp * (1 + target_pct)
                    stoploss_price = ltp * (1 - stoploss_pct)
                    side = 1
                else:
                    target_price = ltp * (1 - target_pct)
                    stoploss_price = ltp * (1 + stoploss_pct)
                    side = -1
                
                # Place bracket order
                order_data = {
                    "symbol": symbol,
                    "qty": quantity,
                    "type": 2,  # Market order
                    "side": side,
                    "productType": "BO",
                    "validity": "DAY",
                    "stopLoss": round(stoploss_price, 2),
                    "takeProfit": round(target_price, 2)
                }
                order_response = self.fyers.place_order(order_data)
                if order_response['code'] != 200:
                    messagebox.showerror("Error", f"Order failed for {symbol}: {order_response['message']}")
                else:
                    messagebox.showinfo("Success", f"Order placed for {symbol}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = Tk()
    app = TradingApp(root)
    root.mainloop()
