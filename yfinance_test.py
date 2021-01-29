import yfinance as yf

msft = yf.Ticker("NIO")
print(msft)
print(msft.info)
print(msft.history(period="max"))