from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes, Application, ConversationHandler
from database import HandleDB
from datetime import datetime
from dotenv import load_dotenv
import os, time


class BotOperations:

	def __init__(self, bot_token:str) -> None:

		self.BOT_TOKEN = bot_token
		self.db = HandleDB("database.db")

	def unixtimeToIsoFormat(self,timestamp:str) -> str:

		dt = datetime.fromtimestamp(int(timestamp))
		formatted = dt.strftime("%Y-%m-%d %H:%M")

		return formatted


	def formatUserDrinks(self, data:list, user_id:str) -> str:

		today_records = []
		today_amount_of_water = 0

		today_date = datetime.today().strftime("%Y-%m-%d")
		bot_reply = "Today progress:\n\n"

		for record in data:
			record_timestamp = self.unixtimeToIsoFormat(record[1])
			record_date = record_timestamp.split(" ")[0]
			record_time = record_timestamp.split(" ")[1]
			amount_of_water = record[0]
			
			if record_date == today_date:
				today_records.append(record)
				today_amount_of_water += int(record[0])
				bot_reply += f"{record_time}  |  {amount_of_water} ml\n"

		user_daily_goal = self.db.selectDataFromUser("daily_goal_ml", "users", user_id)
		progress_percentage = (today_amount_of_water / int(user_daily_goal)) * 100

		bot_reply += f"\n{str(today_amount_of_water)} ml / {user_daily_goal} ml\n\n"
		bot_reply += f"Progress percentage: {progress_percentage:.0f}%"

		if today_amount_of_water == int(user_daily_goal) or today_amount_of_water > int(user_daily_goal):
			user_daily_goals = self.db.userAllDailyGoals(user_id)
			if len(user_daily_goals) == 0:
				self.db.userReachedDailyGoal(user_id)

			else:
				last_daily_goal = user_daily_goals[-1][0]
				formatted = self.unixtimeToIsoFormat(last_daily_goal)

				if formatted.split(" ")[0] != today_date:
					self.db.userReachedDailyGoal(user_id)

			bot_reply += "\n\nCongratulations you hit your daily goal !"

		if bot_reply == "Today progress:\n\n":
			bot_reply += "you don't drink water today !, please use /drink command."


		return bot_reply

	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
		user = update.effective_user

		if not self.db.isUserSignedIn(str(user.id)):

			# add new user to database with default target of 3000 ml
			self.db.addUser(str(user.id), 3000)
			await update.message.reply_html(f" Hi {user.mention_html()} you are using the bot for the first time !, signed with defaul target 3000 ml.")

		await update.message.reply_html(rf"Hi {user.mention_html()} !" )


	async def helpCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

		await update.message.reply_text(
"""					  
/start Initialize the bot and register the user	
									
/setgoal Define your daily hydration target (in ml)
							
/drink Record a water consumption entry
							
/progress Display your current progress toward the daily goal
								
/clear clear all hydration records
							
/help Show commands and usage instructions
""")


	async def setGoalCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

		await update.message.reply_text("Enter new daily goal: ")
		context.user_data["waiting_drink"] = False
		context.user_data["waiting_goal"] = True

	async def drinkCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

		await update.message.reply_text("How much water you drink ?")
		context.user_data["waiting_goal"] = False
		context.user_data["waiting_drink"] = True

	async def progressCommand(self, update:Update, context:ContextTypes.DEFAULT_TYPE) -> None:

		user_id = str(update.effective_user.id)
		user_drinks = self.db.getUserDrinkHistory(user_id)
		await update.message.reply_text(self.formatUserDrinks(user_drinks, user_id))

	
	async def clearCommand(self, update:Update, context:ContextTypes.DEFAULT_TYPE) -> None:
		user_id = str(update.effective_user.id)

		self.db.deleteHydrationRecord(user_id)
		await update.message.reply_text("All hydration records cleared !")



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
				new_goal_query = self.db.selectDataFromUser("daily_goal_ml", "users", user_id)
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
		application.add_handler(CommandHandler("clear", self.clearCommand))

		# chat handler !
		application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.chatHandling))


		application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
	load_dotenv()
	BOT_TOKEN = os.getenv("BOT_TOKEN")

	bot = BotOperations(BOT_TOKEN)

	print("bot started !")
	bot.run()