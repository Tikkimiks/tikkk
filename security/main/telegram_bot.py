# import urllib
#
# import requests
# from telegram import ReplyKeyboardMarkup, KeyboardButton
# from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
# from telegram import InlineKeyboardMarkup, InlineKeyboardButton
# from telegram import Update
# from telegram.ext import Updater, CommandHandler, CallbackContext
# import logging
#
# # Устанавливаем уровень логирования
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
#
# # Функция обработки команды /start
# def start(update, context):
#     if len(context.args) > 0:
#         id_user = context.args[0]
#         chat_id = update.message.chat_id
#         context.user_data['id_user'] = id_user
#         keyboard = [[KeyboardButton("Мои заявки")]]
#         reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
#         response = requests.get(f'http://localhost/diplom/controllers/getChatId.php?chat_id={chat_id}&id_user={id_user}')
#         if response.status_code == 200:
#             update.message.reply_text('Данные успешно сохранены в базе данных')
#         else:
#             update.message.reply_text('Ошибка сохранения данных в базе данных')
#
#         update.message.reply_text('Вы успешно авторизованы. Ваш ID: {}'.format(id_user, chat_id), reply_markup=reply_markup)
#     else:
#         update.message.reply_text('Вы не авторизованы для авторизации зайдите на сайт и перейдите в личный кабинет.')
#
# def my_requests(update, context):
#     id_user = context.user_data.get('id_user')
#     if id_user:
#         url = f'http://localhost/diplom/controllers/getOrderBot.php?id_user={id_user}'
#         response = requests.get(url)
#         if response.status_code == 200:
#             data = response.json()
#             if data:
#                 for order in data:
#                     date = order.get('date')
#                     status = order.get('status')
#                     adress = order.get('adress')
#                     update.message.reply_text(f'Дата: {date}\nСтатус: {status}\nАдрес: {adress}')
#             else:
#                 update.message.reply_text('Нет доступных данных для пользователя с данным ID.')
#         else:
#             update.message.reply_text('Ошибка при запросе данных с сервера.')
#     else:
#         update.message.reply_text('Авторизуйтесь.')
#
#
#
# def send_notification(chat_id, message, id):
#     url = f"https://api.telegram.org/bot{7124867232:AAHgSHNj8e79LofMHPjxvMITnMdeajOFPOo}/sendMessage"
#     data = {'chat_id': chat_id, 'text': message, 'id': id}
#     response = requests.post(url, data=data)
#     return response.json()
#
# def main():
#     # Инициализируем бота с вашим токеном
#     updater = Updater("7124867232:AAHgSHNj8e79LofMHPjxvMITnMdeajOFPOo", use_context=True)
#
#     # Получаем диспетчер для регистрации обработчиков
#     dp = updater.dispatcher
#
#     # Регистрируем обработчики команд
#     dp.add_handler(CommandHandler("start", start, pass_args=True))
#     dp.add_handler(MessageHandler(Filters.text & ~Filters.command, my_requests))
#
#     # Запускаем бота
#     updater.start_polling()
#     updater.idle()
#
# if __name__ == '__main__':
#     main()