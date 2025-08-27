from telegram import Bot


class TelegramBot:
    def __init__(self, token, chatId):
        if token == None or token == "":
            self.bot = None
        else:
            self.bot = Bot(token)
        if chatId == None or chatId == "":
            self.chatId = None
        else:
            self.chatId = chatId

    async def sendMessage(self, text):
       if self.bot == None:
           return
       await  self.bot.send_message(chat_id=self.chatId, text=text)

