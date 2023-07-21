import vk_api
import random
from datetime import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from config import comunity_token, access_token
from vk_api.utils import get_random_id
from data_store import add_user, check_user, delete_user_data
from core import VkTools


class BotInterface:

    def __init__(self, comunity_token, access_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.api = VkTools(access_token)
        self.params = {}
        self.offset = 0
        self.longpoll = VkLongPoll(self.vk)

    def message_send(self, user_id, message, attachment=None):
        # Функция для отправки сообщений бота пользователю

        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()
                        }
                       )

    def event_handler(self):
        # Обработка событий

        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.params = self.api.get_profile_info(event.user_id)
                if event.text.lower() == 'привет' \
                        or event.text.lower() == "hello" \
                        or event.text.lower() == "hi" \
                        or event.text.lower() == "здравствуйте":
                    self.message_send(event.user_id,
                                      f'Приветствую, ' + self.params['name'] + '!\n'
                                      f'Я бот знакомств VKinder!\n'
                                      f'Напишите "Поиск" чтобы начать.\n'
                                      f'Для вызова команд напишите "Команды".'
                                      )
                elif event.text.lower() == 'поиск' or event.text.lower() == 'search':
                    if self.params['city'] is None or self.params['bdate'] is None:
                        self.parameters_refinement(event)
                    self.searching_worksheet(event)

                elif event.text.lower() == 'команды' or event.text.lower() == 'commands':
                    self.params = self.api.get_profile_info(event.user_id)
                    self.message_send(event.user_id,
                                      f'Список команд:\n'
                                      f'"Поиск" - поиск анкет.\n'
                                      f'"Очистка" - очистка анкет из истории поиска.\n'
                                      f'"Пока" - завершение работы бота.')
                # Очистка БД
                elif event.text.lower() == 'очистка' or event.text.lower() == 'clear':
                    delete_user_data(event.user_id)
                    self.message_send(event.user_id,
                                      f'База данных очищена!')
                elif event.text.lower() == 'пока' or event.text.lower() == 'bye':
                    self.message_send(event.user_id,
                                      f'Работа бота завершена.')
                else:
                    self.message_send(event.user_id,
                                      f'Неизвестная команда!\n'
                                      f'Список команд:\n'
                                      f'"Поиск" - поиск анкет.\n'
                                      f'"Очистка" - очистка анкет из истории поиска.\n'
                                      f'"Пока" - завершение работы бота.'
                                      )

    def parameters_refinement(self, event):
        # Функция для сбора недостающих данных о пользователе

        self.message_send(event.user_id, f'Необходимо уточнить некоторые данные...')
        if self.params['city'] is None:
            self.message_send(event.user_id, f'В каком городе хотели бы найти пару?')
            for event_listen in self.longpoll.listen():
                if event_listen.type == VkEventType.MESSAGE_NEW and event_listen.to_me:
                    res = self.api.get_city(event_listen.text.lower())
                    if res == "Error":
                        self.message_send(event_listen.user_id,
                                          f'Вы ввели неизвестный город. В каком городе хотели бы найти пару?')
                    else:
                        self.params['city'] = event_listen.text.lower()
                        break

        if self.params['year'] is None:
            self.message_send(event.user_id, f'Укажите, пожалуйста, полный год вашего рождения')
            for event_listen in self.longpoll.listen():
                if event_listen.type == VkEventType.MESSAGE_NEW and event_listen.to_me:
                    if event_listen.text.lower().isdigit() and len(event_listen.text.lower()) == 4:
                        self.params['year'] = int(datetime.now().today().year) - int(event_listen.text.lower())
                        break
                    else:
                        self.message_send(event.user_id, f'Укажите, пожалуйста, ПОЛНЫЙ ГОД вашего рождения')

    def searching_worksheet(self, event):
        # Поиск анкет пользователя по половой принадлежности

        self.message_send(event.user_id, f'Какой пол ищете МУЖСКОЙ или ЖЕНСКИЙ?')
        for event_listen in self.longpoll.listen():
            if event_listen.type == VkEventType.MESSAGE_NEW and event_listen.to_me:
                if 'женский' in event_listen.text.lower() or 'ж' in event_listen.text.lower():
                    self.params['sex'] = 1
                elif 'мужской' in event_listen.text.lower() or 'м' in event_listen.text.lower():
                    self.params['sex'] = 2
                else:
                    self.message_send(event.user_id,
                                      f'Неизвестная команда. Напишите "женский"/"ж" или "мужской/"м".')
                break
        # получение пользователей по api вк

        users = self.api.search_worksheet(self.params, self.offset)
        self.offset += int(random.randint(1, 10))
        if len(users) == 0:
            self.message_send(event.user_id,
                              f'Поиск пуст. Введите ещё раз "Поиск" с другими параметрами.')
        else:
            worksheet = users.pop()
            users = self.display_users(worksheet, event, users)
            for event_listen_user in self.longpoll.listen():
                if event_listen_user.type == VkEventType.MESSAGE_NEW and event_listen_user.to_me:
                    if 'ещё' in event_listen_user.text.lower() or 'еще' in event_listen_user.text.lower():
                        if len(users) == 0:
                            self.message_send(event.user_id,
                                              f'Анкеты кончились. Введите ещё раз "Поиск".')
                            break
                        else:
                            users = self.display_users(worksheet, event, users)
                            if len(users) == 0:
                                self.message_send(event.user_id,
                                                  f'Анкеты кончились. Введите ещё раз "Поиск".')
                                break
                    elif 'стоп' in event_listen_user.text.lower():
                        self.message_send(event.user_id,
                                          f'Поиск завершён')
                        self.message_send(event.user_id,
                                          f'Список команд:\n'
                                          f'"Поиск" - поиск анкет.\n'
                                          f'"Очистка" - очистка анкет из истории поиска.\n'
                                          f'"Пока" - завершение работы бота.')
                        break
                    else:
                        self.message_send(event.user_id,
                                          f'Неизвестная команда. Напишите "Ещё" или "Стоп".')

    def display_users(self, worksheet, event, users):
        # Функция для вывода анкет в чат. Выводит только те, которых нет в бд

        # проверка наличия в бд
        if check_user(self.params["id"], worksheet["id"]):
            photos = self.api.get_photos(worksheet['id'])
            photo_string = ''
            if photos is not None:
                for photo in photos:
                    photo_string += f'photo{worksheet["id"]}_{photo},'

            self.message_send(event.user_id,
                              f'{worksheet["name"]},\n vk.com/id{worksheet["id"]}',
                              attachment=photo_string
                              )
            add_user(self.params["id"], worksheet["id"])
            if len(users) == 0:
                return []
            else:
                self.message_send(event.user_id,
                                  f'{self.params["name"]}, отправьте "Ещё" чтобы продолжить или "Стоп" чтобы закончить')
                return users
        else:
            # если пользователь есть в бд - берём следующего, если есть в списке
            if len(users) == 0:
                return []
            else:
                worksheet = users.pop()
                users = self.display_users(worksheet, event, users)
                return users


if __name__ == '__main__':
    bot = BotInterface(comunity_token, access_token)
    bot.event_handler()