from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes, Application, ConversationHandler
from database import HandleDB
from datetime import datetime
from dotenv import load_dotenv
import os


class BotOperations:

	def __init__(self, bot_token:str) -> None:

		self.BOT_TOKEN = bot_token
		self.db = HandleDB("database.db")


	def formatUserDrinks(self, data:list) -> str:

		amount = []
		timestamps = []
		formatted_timestamps = []
		formatted_reply = ""

		for record in data:
			amount.append(record[0])
			timestamps.append(record[1])

		for timestamp in timestamps:
		
			dt = datetime.fromtimestamp(int(timestamp))
			formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
			formatted_timestamps.append(formatted_time)


		for i in range(len(formatted_timestamps)):
			formatted_reply += f"{formatted_timestamps[i]} : {amount[i]} ml\n"


		return formatted_reply

		

	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
		user = update.effective_user

		# initialize
		context.user_data["waiting_goal"] = ""
		context.user_data["waiting_drink"] = ""

		if not self.db.isUserSignedIn(str(user.id)):

			# add new user to database with default target of 3000 ml
			self.db.addUser(str(user.id), 3000)
			await update.message.reply_html(f" Hi {user.mention_html()} you are using the bot for the first time !, signed with defaul target 3000 ml.")

		await update.message.reply_html(rf"Hi {user.mention_html()} !" )


	async def helpCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

		await update.message.reply_text(f"Help! {update.message.text}")


	async def setGoalCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
		
		await update.message.reply_text("Enter new daily goal: ")
		context.user_data["waiting_goal"] = True

	async def drinkCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

		await update.message.reply_text("How much water you drink ?")
		context.user_data["waiting_drink"] = True

	async def progressCommand(self, update:Update, context:ContextTypes.DEFAULT_TYPE) -> None:
		
		user_id = str(update.effective_user.id)
		user_drinks = self.db.getUserDrinkHistory(user_id)
		await update.message.reply_text(self.formatUserDrinks(user_drinks))
		


	async def chatHandling(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
		
		user_reply = update.message.text
		user_id = str(update.effective_user.id)

		# new goal prompt
		if context.user_data["waiting_goal"]:
			
			# new entered goal must be digits and less than 4 digits
			# ex. 2000, 2300, 1000
			if user_reply.isdigit() and len(user_reply) <= 4:

				context.user_data["waiting_goal"] = False
				self.db.updateGoal(user_id, int(user_reply))
				new_goal_query = self.db.selectDataFromUser(user_id, "goal_ml")
				await update.message.reply_text(f"daily goal updated to {new_goal_query}!")
				
			else:
				await update.message.reply_text("Please enter correct value for new goal ex. 3000")

		elif context.user_data["waiting_drink"]:

			# input vaildation for new amount of water
			# vaild inputs 300, 200, 214, 10, 20
			if user_reply.isdigit() and len(user_reply) <= 3:

				context.user_data["waiting_drink"] = False
				self.db.userDrinkWater(user_id, user_reply)
				await update.message.reply_text(f"you drink {user_reply} ml of water !")

			else:
				await update.message.reply_text("Please enter correct amount of water ex. 300")

		else:
			await update.message.reply_text("select /help to view all commands.")



	def run(self) -> None:

		application = Application.builder().token(BOT_TOKEN).build()

		# bot active commands !
		application.add_handler(CommandHandler("start", self.start))
		application.add_handler(CommandHandler("help", self.helpCommand))
		application.add_handler(CommandHandler("setgoal", self.setGoalCommand))
		application.add_handler(CommandHandler("drink", self.drinkCommand))
		application.add_handler(CommandHandler("progress", self.progressCommand))

		# chat handler !
		application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chatHandling))

		# run the bot
		application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
	load_dotenv()
	BOT_TOKEN = os.getenv("BOT_TOKEN")

	bot = BotOperations(BOT_TOKEN)

	print("bot started !")
	bot.run()