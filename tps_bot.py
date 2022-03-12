from telegram import ParseMode
from telegram.ext import Updater, CommandHandler,Defaults
from pycoingecko import CoinGeckoAPI
import pandas as pd

cg = CoinGeckoAPI()

TELEGRAM_TOKEN = "5175633314:AAE2EFegd7M6ruGVWNRAGNMDrVnJDGA2ELE"
coinlist = cg.get_coins_list()
def startCommand(update,context):
    context.bot.send_message(chat_id=update.effective_chat.id,text="Starting Price Alert Bot!\nType /help for a list of commands.")

def help(update,context):
    response = '🤖<b> Hello there!\nWelcome to the TPS Price Alert Bot</b>\n\nSee below for a list of commands:\n\n'
    response += '/help - Display a list of commands\n/quote [ticker] - Show current price and data\n <i>(E.g. /quote btc)</i>\n'
    response += '/alert [ticker] [sign] [price] - Create a new alert\n<i>E.g. /alert btc > 60000 to create an alert when BTC goes above $60000</i>\n\n'
    response += '/active - Show list of active alerts'
    response += 'All prices are in USD.'
    context.bot.send_message(chat_id=update.effective_chat.id,text=response)


def priceAlert(update, context):
    if len(context.args) > 2:
        ticker = context.args[0].upper()
        sign = context.args[1]
        price = context.args[2]
        id = get_id(ticker.lower())

        if sign == '<':
            jobname = ticker + ' below 🔻$' + str(price)
            dstring = 'below'
        else:
            jobname = ticker + ' above 🔺$' + str(price)
            dstring = 'above'

        context.job_queue.run_repeating(priceAlertCallback, interval=15, first=10, name = jobname,context=[ticker, sign, price, update.message.chat_id])    
        response = f"⏳ You will be alerted when the price of {ticker} goes {dstring} ${price}. \n"
        response += f"The current price of {ticker} is ${cg.get_price(ids=id,vs_currencies='usd')[id]['usd']}."
    else:
        response = 'Please provide proper ticker and sign.'
    
    context.bot.send_message(chat_id=update.effective_chat.id,text=response)

def priceAlertCallback(context):
    ticker = context.job.context[0]
    sign = context.job.context[1]
    price = context.job.context[2]
    chat_id = context.job.context[3]
    id = get_id(ticker.lower())
    send = False
    spot_price = cg.get_price(ids=id,vs_currencies='usd')[id]['usd']

    if sign == '<':
        if float(price) >= float(spot_price):
            dstring = 'below 🔻'
            send = True
    else:
        if float(price) <= float(spot_price):
            dstring = 'above 🔺'
            send = True

    if send:
        response = f'🔔 {ticker} has gone {dstring} ${price} and has just reached <b>${spot_price}</b>!'
        context.job.schedule_removal()
        context.bot.send_message(chat_id=chat_id, text=response)


def priceQuote(update, context):
    if len(context.args) > 0:
        ticker = context.args[0].upper()
        id = get_id(ticker.lower())
        cg_response = cg.get_price(ids=id,vs_currencies='usd',include_market_cap='true',include_24hr_vol='true',include_24hr_change='true')
        name = get_name(ticker.lower())
        price = cg_response[id]['usd']
        mkt_cap = cg_response[id]['usd_market_cap']
        day_vol = cg_response[id]['usd_24h_vol']
        day_change = cg_response[id]['usd_24h_change']
        response = f"🪙{ticker} - {name}🪙\nUSD Price: ${price:,.2f}\nMarket Cap: ${mkt_cap:,.0f}\n24H Volume: ${day_vol:,.0f}\n24H Change: {day_change:.2f}%\n\n"    
    else:
        response = 'Please provide proper ticker.'
    context.bot.send_message(chat_id=update.effective_chat.id,text=response)

def get_jobs(update,context):
    response = 'Current Active Alerts:\n\n'
    job_names = [job.name for job in context.job_queue.jobs()]
    for i in job_names:
        response += str(i) + '\n'
    context.bot.send_message(chat_id=update.effective_chat.id,text=response)


def get_id(ticker):
    df = pd.DataFrame.from_dict(coinlist)
    if len(df)>0:
        df = df[df['symbol']==ticker].reset_index()
        return df.loc[df['name'] == min(df['name'],key=len)]['id'].values[0]
    else:
        return False

def get_name(ticker):
    df = pd.DataFrame.from_dict(coinlist)
    if len(df)>0:
        df = df[df['symbol']==ticker].reset_index()
        return df.loc[df['name'] == min(df['name'],key=len)]['name'].values[0]
    else:
        return False

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True,defaults=Defaults(parse_mode=ParseMode.HTML))
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("start", startCommand))
    dispatcher.add_handler(CommandHandler("active",get_jobs))
    dispatcher.add_handler(CommandHandler("alert", priceAlert))
    dispatcher.add_handler(CommandHandler("quote", priceQuote))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()