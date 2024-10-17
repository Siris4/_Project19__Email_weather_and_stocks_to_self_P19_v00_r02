import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import yfinance as yf
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz
import os  # To access environment variables

# Your wakeup time (e.g., 9:00 AM)
WAKEUP_TIME = "09:00"
TIMEZONE = "America/New_York"  # Adjust this to your timezone

# Fetch email and API key from environment variables
SENDER_EMAIL = os.getenv('EMAIL_USER')  # Your email from environment variable
SENDER_PASSWORD = os.getenv('EMAIL_PASS')  # Your email password (app password) from environment variable
RECEIVER_EMAIL = SENDER_EMAIL  # Email where you want to receive the daily update (same email in this case)

# Weather API (OpenWeatherMap)
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')  # Your OpenWeatherMap API key from environment variable
LOCATION = 'Monterrey'

# Stock symbols for live financial data
STOCKS = ['AAPL', 'GOOGL', 'AMZN', 'TSLA', 'MSFT']  # Replace with your top 5-10 stock picks


# Function to fetch current weather in Fahrenheit
def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={WEATHER_API_KEY}&units=imperial"
    response = requests.get(url)
    data = response.json()

    if data["cod"] != 200:
        return "Weather information unavailable."

    weather_desc = data['weather'][0]['description'].capitalize()
    temp = data['main']['temp']

    return f"Weather in {LOCATION}: {weather_desc}, {temp}°F"


# Function to fetch current stock prices with error handling
def get_stock_data():
    stock_info = ""
    for stock in STOCKS:
        try:
            ticker = yf.Ticker(stock)
            stock_data = ticker.info
            current_price = stock_data.get('regularMarketPrice', None)

            if current_price is None:
                stock_info += f"{stock}: No current price data available\n"
            else:
                stock_info += f"{stock}: ${current_price:.2f}\n"
        except Exception as e:
            stock_info += f"{stock}: Failed to fetch data ({str(e)})\n"

    return stock_info


# Function to send email
def send_email(weather_info, stock_info):
    msg = MIMEMultipart("alternative")
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"Morning Update - {datetime.now().strftime('%Y-%m-%d')}"

    # Create the email content
    text = f"""
    Good Morning!

    Here is your daily update for {datetime.now().strftime('%Y-%m-%d')}:

    {weather_info}

    Live Stock Prices:
    {stock_info}

    Have a great day!
    """

    msg.attach(MIMEText(text, "plain"))

    # Send the email via Gmail's SMTP server
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


# Scheduler to run every weekday at the specified wake-up time
def schedule_task():
    scheduler = BlockingScheduler(timezone=TIMEZONE)

    @scheduler.scheduled_job('cron', day_of_week='mon-fri', hour=int(WAKEUP_TIME.split(":")[0]),
                             minute=int(WAKEUP_TIME.split(":")[1]))
    def job():
        weather_info = get_weather()
        stock_info = get_stock_data()
        send_email(weather_info, stock_info)

    scheduler.start()


# Manually trigger the job to test it now
if __name__ == "__main__":
    # Manually trigger the job to test it now
    weather_info = get_weather()
    stock_info = get_stock_data()
    send_email(weather_info, stock_info)

    # Run the scheduler to ensure the task will continue to run at the scheduled time
    schedule_task()
