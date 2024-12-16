import requests, asyncio, aiohttp, telebot, json, os
from pymongo import MongoClient
from dotenv import load_dotenv
import threading

load_dotenv()

apiToken = os.getenv('n1lby73TestBot')
db = MongoClient(os.getenv('MONGO_URI'))

bot = telebot.TeleBot(apiToken)
requestTimeout = 60

usersAndLinkCollection = db.get_database().usersAndLink #Table holding both users id and their respective project links

whitelistedUrl = [".onrender.com",".pyhtonanywhere.com", ".netlify.app", "vercel.app"]

def is_whitelisted(link):

    return not any(url in link for url in whitelistedUrl)

    # blackListed = next((url for url in whitelistedUrl if url in link), None)

    # if blackListed:

    #     return False
    
    # else:

    #     return True

#Async function to check link status

async def linkStatus(link):

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(link, time=requestTimeout) as response:

                return response.status
            
    except:

        return None
    
# Function to identify link owner
def whichUser(link):

    whichUsersLink = usersAndLinkCollection.find_one({"usersLink":link})

    if whichUsersLink is None:

        return None
    
    return whichUsersLink.get("usersChatId")
 
# Handle '/start'
def send_welcome(message):

    username = message.chat.username

    response = f'''Hi there @{username}, 
                I'm cron bot and I'm here to help you make your free hosting never sleep.
                use "/help to see available commands'''
    
    bot.reply_to(message, response)
    
# Handle /add
async def add_users_links(message):

    chat_id = str(message.chat.id)
    username = message.chat.username

    try:

        link = message.text.split(maxsplit=1)[1]
        allLinks = [extractedDbLinks for usersLinkDB in usersAndLinkCollection.find()for extractedDbLinks in usersLinkDB.get("usersLink")]

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

            checkWhichUserAddedLink = whichUser(link)

            if checkWhichUserAddedLink == chat_id:

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

                ping = await linkStatus(link)

                if ping == 200:

                    response = f"Adding {link} to our watchlist"
                    bot.reply_to(message, response)

                    chatId = message.chat.id

                    usersAndLinkCollection.update_one(

                        {"usersChatId": str(chatId)},  # Find the user by user_id
                        {"$push": {"usersLink": link}},  # Push new URL to the "urls" array
                        upsert=True  # If the user doesn't exist, create a new document

                    )

                    response = f"successfully added {link}"
                    # bot.reply_to(message, response)

                elif ping == 404:

                    response = f"{link}, returned a 404 error code, kindly look it up"
                    # bot.reply_to(message, response)

                else:

                    response = f"{link}, returned error code {ping}"

                bot.reply_to(message, response)

            except Exception as e:

                response = f"An error occured while addidng {link}, kindly contact support or raise an issue on github"
                bot.reply_to(message, response)

    except IndexError:

        response = "No link attach to command"
        bot.reply_to(message, response)

# Handle /list
def list_users_links(message):

    chat_id = str(message.chat.id)

    try:

        userAddedLinks = usersAndLinkCollection.find_one({"usersChatId":chat_id})

        if len(userAddedLinks.get("usersLink", [])) == 0:

            response = "You have no saved links"

        else:

            response = "Your saved links are:\n\n"

            for user_Links in userAddedLinks.get("usersLink"):

                response += f"- {user_Links}\n"

        bot.reply_to(message, response)
    
    except KeyError:

        response = "You have no saved links"

        bot.reply_to(message, response)
    

# Handle /delete
def delete_users_links(message):

    chat_id = str(message.chat.id)

    try:

        deleteChoice = message.text.split(maxsplit=1)[1]
  
        # Use $pull to remove the specific link from the usersLink array
        result = usersAndLinkCollection.update_one(

            {"usersChatId": chat_id},  # Find the user with the specified usersChatId
            {"$pull": {"usersLink": deleteChoice}}  # Remove target_link from the usersLink array
            
        )

        if result.modified_count > 0: #modified_count is inbuilt to pymongo to check number of iles deleted

            response = f"Deleted {deleteChoice}"

        else:

            response = f"{deleteChoice} is not in your list of links"

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

    # Check if the link ends with "/" and remove it
    if command.endswith("/"):

        command = command[:-1]  

    #get function to be called
    handler = command_handlers.get(command.split()[0])

    if handler:
        handler(message)

    else:

        response = "Sorry, I don't understand that command."
        bot.reply_to(message, response)

# Track all messages that does not have the correct message syntax which is /
@bot.message_handler(func=lambda userMessage: not userMessage.text.startswith('/'))
def handle_wrong_msgFormat(message):

    if ((message.text.lower() == os.getenv('adminPrompt')) and (str(message.chat.id) == os.getenv('adminId'))):

        response = "what would you like to broadcast"
        
    response = "Seems you're trying to send a command kindly use the right format or use '/help' to see list of available commands"

    bot.reply_to(message, response)

async def processLinks():

    allLinks = [extractedDbLinks for usersLinkDB in usersAndLinkCollection.find()for extractedDbLinks in usersLinkDB.get("usersLink")]

    try:

        for links in allLinks:

            response = await linkStatus(links)

            if response != 200:

                linkOwner = whichUser(links)

                botResponse = f"Hello, your link:\n\n{links}\n\ndid not return a 200 response code after pinging"
                bot.send_message(linkOwner, botResponse)

# Handle request exception (e.g., timeout, connection error)
    except requests.RequestException:
            
            linkOwner = whichUser(links)

            botResponse = f"Hello, your link:\n\n{links}\n\ncould not be reached due to a service timeout or connection error.\n\nKindly reach out for support https://github.com/n1lby73/cron/issues if the error persists."
            bot.send_message(linkOwner, botResponse)

# Async function to start pinging the links
    
async def pingLinks(interval):
    while True:
        await processLinks()
        print ("here")
        await asyncio.sleep(interval)

def run_ping_task():
    # This function runs the asyncio event loop for pinging
    asyncio.run(pingLinks(300)) 

# # Async funtion to start bot
# async def startBot():

#     bot.infinity_polling()

# async def main():

#     botTask = asyncio.create_task(startBot())
#     pingTask = asyncio.create_task(pingLinks(300))

#     await asyncio.gather(botTask, pingTask)

# asyncio.run(main())
# Start pingLinks in a separate thread
        
ping_thread = threading.Thread(target=run_ping_task)
ping_thread.daemon = True  # Set as daemon thread to stop when main thread stops
ping_thread.start()

bot.infinity_polling()
