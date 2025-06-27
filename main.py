from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes, Application, ConversationHandler
from database import HandleDB
from datetime import datetime
from dotenv import load_dotenv
import os, json


class BotOperations:

	def __init__(self, bot_token:str) -> None:

		self.BOT_TOKEN = bot_token
		self.db = HandleDB("database.db")

		# load bot replys
		with open('ui_responses.json', 'r', encoding='utf-8') as file:
			self.bot_replys = json.load(file)

	def unixtimeToIsoFormat(self,timestamp:str) -> str:

		dt = datetime.fromtimestamp(int(timestamp))
		formatted = dt.strftime("%Y-%m-%d %H:%M")

		return formatted


	def formatUserDrinks(self, data:list, user_id:str) -> str:

		today_records = []
		today_amount_of_water = 0

		today_date = datetime.today().strftime("%Y-%m-%d")
		bot_reply = f"{self.bot_replys["en"]["daily_progress_title"]}\n\n"

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

		bot_reply += f"\n{self.bot_replys["en"]["progress_percentage"].replace("#today_amount_of_water#", str(today_amount_of_water)).replace("#user_daily_goal#", user_daily_goal)}\n\n"
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

			bot_reply += f"\n\n{self.bot_replys["en"]["daily_goal_reached"]}"

		if bot_reply == f"{self.bot_replys["en"]["daily_progress_title"]}\n\n":
			bot_reply += self.bot_replys["en"]["daily_progress_empty"]


		return bot_reply

	async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
		user = update.effective_user

		if not self.db.isUserSignedIn(str(user.id)):

			# add new user to database with default target of 2000 ml
			self.db.addUser(str(user.id), 2000)
			await update.message.reply_html(self.bot_replys["en"]["register_welcome"].replace("#username#", f"@{user.username}") + "\n\n" + self.bot_replys["en"]["help"])

		else: await update.message.reply_text(self.bot_replys["en"]["login_welcome"].replace("#username#", f"@{user.username}"))


	async def helpCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

		await update.message.reply_text(self.bot_replys["en"]["help"])


	async def setGoalCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

		await update.message.reply_text(self.bot_replys["en"]["set_goal_prompt"])
		context.user_data["waiting_drink"] = False
		context.user_data["waiting_goal"] = True

	async def drinkCommand(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

		await update.message.reply_text(self.bot_replys["en"]["drink_prompt"])
		context.user_data["waiting_goal"] = False
		context.user_data["waiting_drink"] = True

	async def progressCommand(self, update:Update, context:ContextTypes.DEFAULT_TYPE) -> None:

		user_id = str(update.effective_user.id)
		user_drinks = self.db.getUserDrinkHistory(user_id)
		await update.message.reply_text(self.formatUserDrinks(user_drinks, user_id))

	
	async def clearCommand(self, update:Update, context:ContextTypes.DEFAULT_TYPE) -> None:
		user_id = str(update.effective_user.id)

		self.db.deleteHydrationRecord(user_id)
		await update.message.reply_text(self.bot_replys["en"]["clear_prompt"])



	async def chatHandling(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
		
		user_reply = update.message.text
		user_id = str(update.effective_user.id)

		# new goal prompt
		if context.user_data["waiting_goal"]:
			
			# new entered goal must be digits and less than 4 digits
			# ex. 2000, 2300, 1000
			if user_reply.isdigit() and len(user_reply) <= 4 and user_reply[0] != "0":
				
				context.user_data["waiting_goal"] = False
				self.db.updateGoal(user_id, int(user_reply))
				new_goal_query = self.db.selectDataFromUser("daily_goal_ml", "users", user_id)
				await update.message.reply_text(self.bot_replys["en"]["goal_success"].replace("#new_goal#", new_goal_query))
				
			else:
				await update.message.reply_text(self.bot_replys["en"]["goal_fail"])

		elif context.user_data["waiting_drink"]:

			# input vaildation for new amount of water
			# vaild inputs 300, 200, 214, 10, 20
			if user_reply.isdigit() and len(user_reply) <= 3 and user_reply[0] != "0":

				context.user_data["waiting_drink"] = False
				self.db.userDrinkWater(user_id, user_reply)
				await update.message.reply_text(self.bot_replys["en"]["drink_success"].replace("#amount_of_water_ml#", user_reply))

			else:
				await update.message.reply_text(self.bot_replys["en"]["drink_fail"])

		else:
			await update.message.reply_text(self.bot_replys["en"]["chat_fail"])



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