import tkinter as tk
from tkinter import messagebox
import argparse
from fyers_apiv3 import fyersModel
import math

# Function to place bracket orders
def place_orders(total_investment, stocks, target_pct, stoploss_pct, side, access_token, app_id):
    """
    Place intraday bracket orders for the given stocks using Fyers API.
    
    Parameters:
    - total_investment: Total amount to invest
    - stocks: List of stock symbols
    - target_pct: Target percentage
    - stoploss_pct: Stop-loss percentage
    - side: 'buy' or 'sell'
    - access_token: Fyers API access token
    - app_id: Fyers App ID
    """
    # Initialize Fyers API client
    fyers = fyersModel.FyersModel(token=access_token, client_id=app_id)
    
    # Get current prices for the stocks
    symbols = ','.join(stocks)
    quotes = fyers.quotes({'symbols': symbols})
    if quotes['s'] != 'ok':
        raise Exception("Failed to fetch quotes: " + quotes.get('message', 'Unknown error'))
    prices = {quote['v']['symbol']: quote['v']['lp'] for quote in quotes['d']}
    
    # Calculate investment per stock
    num_stocks = len(stocks)
    investment_per_stock = total_investment / num_stocks
    
    # Calculate quantity for each stock
    quantities = {}
    for stock in stocks:
        if stock not in prices:
            print(f"Price not found for {stock}, skipping.")
            continue
        price = prices[stock]
        quantity = math.floor(investment_per_stock / price)
        quantities[stock] = quantity
    
    # Calculate stop-loss and target prices based on buy/sell
    if side == 'buy':
        sl_multiplier = 1 - stoploss_pct / 100
        target_multiplier = 1 + target_pct / 100
    else:  # sell
        sl_multiplier = 1 + stoploss_pct / 100
        target_multiplier = 1 - target_pct / 100
    
    # Place bracket orders
    for stock in stocks:
        quantity = quantities.get(stock, 0)
        if quantity == 0:
            print(f"Quantity for {stock} is zero, skipping.")
            continue
        current_price = prices[stock]
        sl_price = current_price * sl_multiplier
        target_price = current_price * target_multiplier
        sl_price = round(sl_price, 2)
        target_price = round(target_price, 2)
        
        order_data = {
            'symbol': stock,
            'qty': quantity,
            'type': 2,  # Market order
            'side': 1 if side == 'buy' else -1,
            'productType': 'BO',  # Bracket Order
            'limitPrice': 0,  # Market order
            'stopPrice': 0,
            'validity': 'DAY',  # Intraday
            'stopLoss': sl_price,
            'takeProfit': target_price,
            'offlineOrder': 'False',
            'disclosedQty': 0
        }
        response = fyers.place_order(order_data)
        if response['s'] == 'ok':
            print(f"Order placed successfully for {stock}: {response}")
        else:
            print(f"Failed to place order for {stock}: {response.get('message', 'Unknown error')}")

# GUI function
def create_gui(app_id):
    """Create a Tkinter-based GUI for the trading app."""
    root = tk.Tk()
    root.title("Fyers Algo Trading")
    
    # Access token field
    tk.Label(root, text="Access Token:").grid(row=0, column=0, pady=5)
    token_entry = tk.Entry(root, width=50)
    token_entry.grid(row=0, column=1, pady=5)
    
    # Total investment field
    tk.Label(root, text="Total Investment (INR):").grid(row=1, column=0, pady=5)
    total_investment_entry = tk.Entry(root)
    total_investment_entry.grid(row=1, column=1, pady=5)
    
    # Stocks list field
    tk.Label(root, text="Stocks (e.g., NSE:TATAMOTORS-EQ, one per line):").grid(row=2, column=0, pady=5)
    stocks_text = tk.Text(root, height=10, width=30)
    stocks_text.grid(row=2, column=1, pady=5)
    
    # Target percentage field
    tk.Label(root, text="Target %:").grid(row=3, column=0, pady=5)
    target_entry = tk.Entry(root)
    target_entry.grid(row=3, column=1, pady=5)
    
    # Stop-loss percentage field
    tk.Label(root, text="Stop-loss %:").grid(row=4, column=0, pady=5)
    stoploss_entry = tk.Entry(root)
    stoploss_entry.grid(row=4, column=1, pady=5)
    
    # Buy or Sell option
    side_var = tk.StringVar(value="buy")
    tk.Radiobutton(root, text="Buy", variable=side_var, value="buy").grid(row=5, column=0, pady=5)
    tk.Radiobutton(root, text="Sell", variable=side_var, value="sell").grid(row=5, column=1, pady=5)
    
    # Submit button
    def submit():
        try:
            access_token = token_entry.get().strip()
            total_investment = float(total_investment_entry.get())
            stocks = [s.strip() for s in stocks_text.get("1.0", tk.END).strip().split('\n') if s.strip()]
            target_pct = float(target_entry.get())
            stoploss_pct = float(stoploss_entry.get())
            side = side_var.get()
            if not access_token:
                raise ValueError("Access token is required.")
            if not stocks:
                raise ValueError("At least one stock must be specified.")
            place_orders(total_investment, stocks, target_pct, stoploss_pct, side, access_token, app_id)
            messagebox.showinfo("Success", "Orders placed successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    tk.Button(root, text="Submit", command=submit).grid(row=6, column=0, columnspan=2, pady=10)
    root.mainloop()

# Main execution
if __name__ == '__main__':
    # Provided API credentials
    APP_ID = "RX6DYO4KLQ-100"
    
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Fyers Algo Trading App")
    parser.add_argument('--total', type=float, help="Total investment amount")
    parser.add_argument('--stocks', type=str, help="Comma-separated list of stocks")
    parser.add_argument('--target', type=float, help="Target percentage")
    parser.add_argument('--stoploss', type=float, help="Stop-loss percentage")
    parser.add_argument('--side', type=str, choices=['buy', 'sell'], help="Buy or sell")
    parser.add_argument('--token', type=str, help="Fyers access token")
    args = parser.parse_args()
    
    # Check if CLI arguments are provided
    if all([args.total, args.stocks, args.target, args.stoploss, args.side, args.token]):
        stocks = [s.strip() for s in args.stocks.split(',') if s.strip()]
        place_orders(args.total, stocks, args.target, args.stoploss, args.side, args.token, APP_ID)
    else:
        # Launch GUI if no arguments are provided
        create_gui(APP_ID)