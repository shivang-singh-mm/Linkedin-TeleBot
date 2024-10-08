import telebot
from linkedin_automation import run_linkedin_automation

bot = telebot.TeleBot('7774896882:AAF98EDAMGLfuAAHvLW_bHl1Ovg44pxiOes')


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use /apply to start applying for jobs on LinkedIn.")


@bot.message_handler(commands=['apply'])
def handle_apply(message):
    bot.reply_to(message, "Please provide your LinkedIn cookies in the format: li_at=VALUE;JSESSIONID=VALUE")
    bot.register_next_step_handler(message, process_cookies)


def process_cookies(message):
    cookie_string = message.text
    cookies = [{'name': cookie.split('=')[0], 'value': cookie.split('=')[1]} for cookie in cookie_string.split(';')]
    bot.reply_to(message, "Cookies received. Please provide the job search keyword.")
    bot.register_next_step_handler(message, lambda m: start_job_application(m, cookies))


def start_job_application(message, cookies):
    search_keyword = message.text
    bot.reply_to(message, f"Starting job application process for keyword: {search_keyword}")
    try:
        result = run_linkedin_automation(cookies, search_keyword)
        bot.reply_to(message, result)
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")


if __name__ == "__main__":
    bot.polling()
