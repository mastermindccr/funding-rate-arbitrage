# What is this project about?

## Strategy
- The bot will use Binance API to monitor the funding rate of all the perpetual futures contracts and select the ones with the highest funding rate. The bot will then buy the pair in spot market and short the equivalent amount in the futures market to earn the funding rate. The bot will also send a notification to LINE notify when the bot makes a trade.
- When the bot detect the funding rate is lower than the threshold(0.01%), the bot will find the next profitable token pair.

## Risk management
- Assume the entry price is X, the liquidation price is Y, if the bot detect the price is going to reach Y ($P\ge(Y-X)*0.8+X$), the bot will close the position in both markets to prevent liquidation.

# How to run the code?
1. `pip -r requirements.txt` to install the dependencies
2. fill in the following information in `.env` file:
```
API_KEY=<Binance_API_key>
SECRET=<Binance_API_secret>
LINE_NOTIFY_TOKEN=<token>
```
3. run `python main.py` to start the bot

# Others
- The bot will not work if the funding rate is lower than the threshold(0.01%)
- `encrypt.py` is used to encrypt the API key and secret, while `decrypt.py` is used to decrypt the API key and secret. If you want to deploy the bot on entrusted server, you can use these two files to encrypt the API key and secret then decrypt them in `main.py`.