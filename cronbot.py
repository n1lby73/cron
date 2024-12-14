from pymongo import MongoClient
from dotenv import load_dotenv
import threading
import requests
import telebot
import json
import os

load_dotenv()

apiToken = os.getenv('n1lby73TestBot')
db = MongoClient(os.getenv('MONGO_URI'))

bot = telebot.TeleBot(apiToken)
requestTimeout = 60

usersAndLinkCollection = db.get_database().usersAndLink


# Load existing JSON data (if any)
try:

    with open('usersAndLink.json', 'r') as file:

        chat_data = json.load(file)

except FileNotFoundError:

    chat_data = {}

whitelistedUrl = [".onrender.com",".pyhtonanywhere.com", ".netlify.app", "vercel.app"]

def is_whitelisted(link):

    blackListed = next((url for url in whitelistedUrl if url in link), None)

    if blackListed:

        return False
    
    else:

        return True
    # for url in whitelistedUrl:

    #     if url in link:

    #         return False
        
    # return True

# Handle '/start'
def send_welcome(message):

    username = message.chat.username

    response = f'''Hi there @{username}, 
                I'm cron bot and I'm here to help you make your free hosting never sleep.
                use "/help to see available commands'''
    
    bot.reply_to(message, response)
    
# Handle /add
def add_users_links(message):

    chat_id = message.chat.id
    username = message.chat.username

    try:

        link = message.text.split(maxsplit=1)[1]
        allLinks = [links for usersLinks in chat_data.values() for links in usersLinks]

        if not link.startswith(("http","https")):

            response = "Please use either https or http format"

            bot.reply_to(message, response)
        
        elif any (x.isdigit() for x in link):

            response = "local server URL not accepted"

            bot.reply_to(message, response)

        elif "www" in link:

            response = "Url provided does not match that of a hosted project"

            bot.reply_to(message, response)

        elif link in allLinks:

            usersLink = chat_data[str(chat_id)]
                    
            for users_link in usersLink:

                if users_link == link:

                    response = f"Dear @{username}, you've already added {link} to your collection\n\nKindly use '/list' command to see the list of all links you've added"
                    bot.reply_to(message, response)

                    return #To stop the program execution

            response = f"{link} has already been added to our watchlist by another user"

            bot.reply_to(message, response)

        elif is_whitelisted(link):

            response = "This is a blacklisted url,\n\nKindly raise an issue https://github.com/n1lby73/cron/issues if you think it's a mistake."

            bot.reply_to(message, response)

        else:

            try:

                response = "Kindly hold on while we confirm link authenticity"

                bot.reply_to(message, response)

                ping = requests.get(link, timeout=requestTimeout)

                if ping.status_code == 200:

                    response = f"Adding {link} to our watchlist"
                    bot.reply_to(message, response)

                    chatId = message.chat.id

                    if str(chatId) in chat_data:
                        
                        document = {str(chatId): [link]}
                        # usersAndLinkCollection.insert_one(document)
                        usersAndLinkCollection.update_one(
                            {"usersChatId": str(chatId)},  # Find the user by user_id
                            {"$push": {"usersLink": link}},  # Push new URL to the "urls" array
                            upsert=True  # If the user doesn't exist, create a new document
                        )

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

                elif ping.status_code == 404:

                    response = f"{link}, returned a 404 error code, kindly look it up"
                    bot.reply_to(message, response)

                else:

                    response = f"{link}, returned error code {ping.status_code}"

            except Exception as e:
                print(str(e))
                response = f"An error occured while addidng {link}, kindly contact support or raise an issue on github"
                bot.reply_to(message, response)

    except IndexError:

        response = "No link attach to command"
        bot.reply_to(message, response)

# Handle /list
def list_users_links(message):

    chat_id = message.chat.id

    try:

        usersLink = chat_data[str(chat_id)]

        if len(usersLink) == 0:

            response = "You have no saved links"

            bot.reply_to(message, response)

        else:

            response = "Your saved links are:\n\n"

            for user_Links in usersLink:

                response += f"- {user_Links}\n"

            bot.reply_to(message, response)
    
    except KeyError:

        response = "You have no saved links"

        bot.reply_to(message, response)
    

# Handle /delete
def delete_users_links(message):

    chat_id = message.chat.id

    try:

        deleteChoice = message.text.split(maxsplit=1)[1]

        usersLink = chat_data[str(chat_id)]
                    
        for users_link in usersLink:

            if users_link == deleteChoice:

                chat_data[str(chat_id)].remove(users_link)
                
                with open('usersAndLink.json', 'w') as file:
                    json.dump(chat_data, file, indent=4)

                response = f"Deleted {deleteChoice}"
                bot.reply_to(message, response)
                    
    except:

        response = "No link attached to command"
        bot.reply_to(message, response)

# Handle /help
def send_help(message):

    response = "Available commands are: \n\n/help ==> print this help message\n/list ==> list all added links\n/add <url> ==> add link\n/delete <url> ==> delete links"

    bot.reply_to(message, response)


# Define a dictionary mapping commands to their handler functions
command_handlers = {

    "/start": send_welcome,

    "/add": add_users_links,

    "/list": list_users_links,

    "/delete": delete_users_links,

    "/help": send_help

}

# Track all messages sent to the bot in other to handle commands with upper or mixed case
@bot.message_handler(func=lambda userMessage: userMessage.text.startswith('/'))
def handle_commands(message):

    # Force the command to be lowercase
    command = message.text.lower()

    #get function to be called
    handler = command_handlers.get(command.split()[0])

    if handler:
        handler(message)

    elif handler == "/add" or handler == "/delete":
        
        linkToAddOrDelete = command.split(" ",1)

        if handler == "/add":

            add_users_links(linkToAddOrDelete)

        if handler == "/delete":

            delete_users_links(linkToAddOrDelete)

    else:

        response = "Sorry, I don't understand that command."
        bot.reply_to(message, response)

# Track all messages that does not have the correct message syntax which is /
@bot.message_handler(func=lambda userMessage: not userMessage.text.startswith('/'))
def handle_wrong_msgFormat(message):

    response = "Seems you're trying to send a command kindly use the right format or use '/help' to see list of available commands"

    bot.reply_to(message, response)

# Function to identify link owner

def linkOwnerbylink(link):

    for linkOwner, linkOwned in chat_data.items():

        return next((linkOwner for confirmLinkedOwned in linkOwned if confirmLinkedOwned == link), None)

        # for confirmLinkedOwned in linkOwned:

        #     if confirmLinkedOwned == link:

        #         return linkOwner
    
def processLinks():

    allLinks = [links for usersLinks in chat_data.values() for links in usersLinks]

    try:

        for links in allLinks:

            response = requests.get(links, timeout=requestTimeout)

            if response.status_code != 200:

                linkOwner = linkOwnerbylink(links)

                botResponse = f"Hello, your link:\n\n{links}\n\ndid not return a 200 response code after pinging"
                bot.send_message(linkOwner, botResponse)

# Handle request exception (e.g., timeout, connection error)
    except requests.RequestException:
            
            linkOwner = linkOwnerbylink(links)

            botResponse = f"Hello, your link:\n\n{links}\n\ncould not be reached due to a service timeout or connection error.\n\nKindly reach out for support https://github.com/n1lby73/cron/issues if the error persists."
            bot.send_message(linkOwner, botResponse)

# Function to start ping as a thread
    
def pingLinks(interval):
    import time
    while True:
        processLinks()
        time.sleep(interval)

# Start pingLinks in a separate thread
        
ping_thread = threading.Thread(target=pingLinks, args=(300,))
ping_thread.daemon = True  # Set as daemon thread to stop when main thread stops
ping_thread.start()

bot.infinity_polling()
# pingLinks(1)