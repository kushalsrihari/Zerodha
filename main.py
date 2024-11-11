from kiteconnect import KiteConnect
import time

# Zerodha Kite API setup
api_key = "your_api_key"
access_token = "your_access_token"
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Configuration
STOP_LOSS_PERCENTAGE = 0.75 / 100  # 0.75% stop loss
TARGET_PERCENTAGE = 1.2 / 100      # 1.2% target
ENTRY_PRICE_DISCOUNT = 0.05 / 100  # 0.05% below current price
INITIAL_FUNDS = 15000              # Available funds in INR

# Placeholder function to read stock list from SMS
def fetch_stock_list_from_sms():
    # Example return, replace with actual SMS reading logic
    return ["RELIANCE", "TCS", "INFY"]

# Divide funds across stocks and calculate quantity
def calculate_quantity(stock_price, funds, stock_count):
    total_allocated = funds / stock_count
    quantity = int(total_allocated / stock_price)
    return quantity

# Monitor and execute trade logic
def monitor_stocks(stock_list):
    while stock_list:
        for stock in stock_list:
            # Fetch current price
            current_price = kite.ltp(f"NSE:{stock}")["NSE:" + stock]["last_price"]
            entry_price = current_price * (1 - ENTRY_PRICE_DISCOUNT)

            # Calculate quantity
            quantity = calculate_quantity(entry_price, INITIAL_FUNDS, len(stock_list))

            # Place buy order
            order_id = kite.place_order(
                tradingsymbol=stock,
                exchange="NSE",
                transaction_type="BUY",
                quantity=quantity,
                order_type="LIMIT",
                price=entry_price,
                product="MIS"  # Margin Intraday Square-off
            )

            print(f"Bought {quantity} of {stock} at {entry_price}")

            # Monitor for target or stop loss
            bought_price = entry_price
            while True:
                current_price = kite.ltp(f"NSE:{stock}")["NSE:" + stock]["last_price"]
                profit_price = bought_price * (1 + TARGET_PERCENTAGE)
                loss_price = bought_price * (1 - STOP_LOSS_PERCENTAGE)

                if current_price >= profit_price:
                    # Place sell order for profit
                    kite.place_order(
                        tradingsymbol=stock,
                        exchange="NSE",
                        transaction_type="SELL",
                        quantity=quantity,
                        order_type="MARKET",
                        product="MIS"
                    )
                    print(f"Sold {stock} at {current_price} for target profit")
                    stock_list.remove(stock)
                    break
                elif current_price <= loss_price:
                    # Place sell order for stop loss
                    kite.place_order(
                        tradingsymbol=stock,
                        exchange="NSE",
                        transaction_type="SELL",
                        quantity=quantity,
                        order_type="MARKET",
                        product="MIS"
                    )
                    print(f"Sold {stock} at {current_price} for stop loss")
                    stock_list.remove(stock)
                    break

                time.sleep(5)  # Wait before checking prices again

# Fetch stock list from SMS
stock_list = fetch_stock_list_from_sms()

# Monitor all stocks concurrently
monitor_stocks(stock_list)
