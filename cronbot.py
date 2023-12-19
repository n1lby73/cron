from dotenv import load_dotenv
import requests
import telebot
import json
import os

load_dotenv()

apiToken = os.getenv('n1lby73TestBot')
bot = telebot.TeleBot(apiToken)

# Load existing JSON data (if any)
try:

    with open('usersAndLink.json', 'r') as file:

        chat_data = json.load(file)

except FileNotFoundError:

    chat_data = {}

# blacklistedUrl = ["github", "google", "instagram", "facebook", "twitter", "snapchat"]

# def is_blacklisted(link):
#     for url in blacklistedUrl:
#         if url in link:
#             return True
#     return False

# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):

    chat_id = message.chat.id
    username = message.chat.username

    response = f'''Hi there @{username}, 
                I'm cron bot and I'm here to help you make your free hosting never sleep.
                use "/add <your project base link>" to add your project to our watchlist'''
    
    bot.reply_to(message, response)
    
# Handle /add
@bot.message_handler(commands=['add'])
def add_users_links(message):
    try:

        link = message.text.split(maxsplit=1)[1]

        if not link.startswith(("http","https")):

            response = "Please use either https or http format"

            bot.reply_to(message, response)
        
        elif any (x for x in link if x in ["1","2","3","4","5","6","7","8","9","0"]):

            response = "local server URL not accepted"

            bot.reply_to(message, response)

        # elif is_blacklisted(link):

        #     response = "the link is blacklisted"

        #     bot.reply_to(message, response)

        else:

            try:

                response = "kindly hold on while we confirm link authenticity"

                bot.reply_to(message, response)

                ping = requests.get(link)

                if ping.status_code == 200:

                    response = f"Adding {link} to our watchlist"
                    bot.reply_to(message, response)

                    chatId = message.chat.id

                    if str(chatId) in chat_data:

                        chat_data[str(chatId)].append(link)

                        # Update the JSON file with the new data
                        with open('usersAndLink.json', 'w') as file:
                            json.dump(chat_data, file, indent=4)

                        response = f"successfully added {link}"
                        bot.reply_to(message, response)

                    else:

                        chat_data[str(chatId)] = []
                        chat_data[str(chatId)].append(link)

                        # Update the JSON file with the new data
                        with open('usersAndLink.json', 'w') as file:
                            json.dump(chat_data, file, indent=4)

                        response = f"successfully added {link}"
                        bot.reply_to(message, response)

            except:

                print(f"Failed to send message")
                response = f"{link} is not a valid link"
                bot.reply_to(message, response)

    except IndexError:

        response = "No link attach to command"
        bot.reply_to(message, response)

# Handle /list
@bot.message_handler(commands=['list'])
def add_users_links(message):

    chat_id = message.chat.id
    username = message.chat.username

    usersLink = chat_data[str(chat_id)]

    response = "Your saved links:\n\n"

    for user_Links in usersLink:

        response += f"- {user_Links}\n"

    bot.reply_to(message, response)

bot.infinity_polling()