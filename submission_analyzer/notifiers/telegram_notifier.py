from telegram import Bot


class TelegramBot:
    def __init__(self, token, chatId):
        if token == None:
            raise ValueError("token is not set in .env")
        if chatId == None:
            raise ValueError("chat id is not set in .env")
        self.bot = Bot(token)
        self.chatId = chatId

    async def sendMessage(self, text):
       await  self.bot.send_message(chat_id=self.chatId, text=text)

