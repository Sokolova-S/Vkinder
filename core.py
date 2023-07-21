from datetime import datetime
import vk_api 
from vk_api.exceptions import ApiError

from config import access_token, comunity_token


def _bdate_to_year(bdate):
    # Вычисление возраста
    if not bdate:
        return None
    else:
        today = datetime.now().today()
        date = datetime.strptime(bdate, '%d.%m.%Y')
        return int(today.year - date.year - ((today.month, today.day) < (date.month, date.day)))



class VkTools:

    def __init__(self, access_token):
        self.api = vk_api.VkApi(
            login='',
            password='',
            token=access_token
        )

    def get_profile_info(self, user_id):
        # Получение информации о профиле

        try:
            info, = self.api.method(
                'users.get',
                {
                    'user_ids': user_id,
                    'fields': ['city', 'bdate','sex','relation','home_town']
                }
            )
        except ApiError as e:
            info = {}
            print(f'ApiError = {e}')

        result = {
            'id': info['id'],
            'name': (info['first_name'] + ' ' + info['last_name']) if 'first_name' in info and 'last_name' in info else None,
            'sex': info.get('sex'),
            'city': info.get('city')['title'] if info.get('city') is not None else None,
            'year': _bdate_to_year(info.get('bdate')),
            'bdate': info.get('bdate')
        }
        print(result)
        return result

    def get_city(self, city_name):
        # Получение отсутствующего города в профиле

        res = ""
        city_name = (city_name[:15]) if len(city_name) > 15 else city_name
        cities = self.api.method("database.getCities",
                                 {'items': 0,
                                  'city_name': city_name,
                                  'count': 10,
                                  'offset': 0,
                                  'q': city_name,
                                  'need_all': True
                                  }
                                 )
        try:
            cities = cities['items']
        except KeyError as e:
            print(f'KeyError = {e}')
            cities = []
        for city in cities:
            if city_name.lower() == city['title'].lower():
                res = city['title']
        return res if res != "" else "Error"

    def search_worksheet(self, param, offset):
        # Поиск анкет

        try:
            users = self.api.method(
                'users.search',
                {
                    'count': 1000,
                    'offset': offset,
                    'hometown': param['city'],
                    'sex': param['sex'],
                    'has_photo': True,
                    # 'age_from': param['year'] - 3,
                    # 'age_to': param['year'] + 5,
                    'status': '1',
                    'sort': '0'
                }
            )
            try:
                users = users['items']
            except KeyError:
                return []
        except ApiError as e:
            users = []
            print(f'ApiError = {e}')
        result = []
        for user in users:
            if user['is_closed'] is False:
                result.append({'id': user['id'],
                               'name': user['first_name'] + ' ' + user['last_name'],
                               'is_closed': user['is_closed']
                               })
        return result

    def get_photos(self, user_id):
        # Получение фото профиля с наибольшим количеством лайков

        try:
            photos = self.api.method('photos.get',
                                     {'owner_id': user_id,
                                      'album_id': 'profile',
                                      'extended': 1,
                                      'count': 3
                                      })

        except KeyError as e:
            photos = {}
            print(f'KeyError = {e}')

        if photos.get('items'):
            users = [(item['id'], item['likes']['count'] + item['comments']['count']) for item in photos['items']]
            users_top = [k[0] for k in sorted(users, key=lambda d: d[1], reverse=True)][:3]
            return users_top


if __name__ == '__main__':
    user_id = 
    tools = VkTools(access_token)
    params = tools.get_profile_info(user_id)
    worksheets = tools.search_worksheet(params, 20)
    if worksheets:
        for worksheet in worksheets:
            photos = tools.get_photos(worksheet['id'])
                    
            # bot = BotInterface(comunity_token, access_token)
            # bot.event_handler()

        print(worksheets)
