import random
from time import time, localtime
import cityinfo
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os
import linecache


def get_color():
    # 获取随机颜色
    get_colors = lambda n: list(map(lambda i: "#" + "%06x" % random.randint(0, 0xFFFFFF), range(n)))
    color_list = get_colors(100)
    return random.choice(color_list)


def get_access_token():
    # appId
    app_id = config["app_id"]
    # appSecret
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        access_token = get(post_url).json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        os.system("pause")
        sys.exit(1)
    # print(access_token)
    return access_token


def get_weather(province, city):
    # 城市id
    try:
        city_id = cityinfo.cityInfo[province][city]["AREAID"]
    except KeyError:
        print("推送消息失败，请检查省份或城市是否正确")
        os.system("pause")
        sys.exit(1)
    # city_id = 101280101
    # 毫秒级时间戳
    t = (int(round(time() * 1000)))
    headers = {
        "Referer": "http://www.weather.com.cn/weather1d/{}.shtml".format(city_id),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    url = "http://d1.weather.com.cn/dingzhi/{}.html?_={}".format(city_id, t)
    response = get(url, headers=headers)
    response.encoding = "utf-8"
    response_data = response.text.split(";")[0].split("=")[-1]
    response_json = eval(response_data)
    # print(response_json)
    weatherinfo = response_json["weatherinfo"]
    # 天气
    weather = weatherinfo["weather"]
    # 最高气温
    temp = weatherinfo["temp"]
    # 最低气温
    tempn = weatherinfo["tempn"]
    return weather, temp, tempn


def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 今年生日
        birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
        year_date = birthday


    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    if today > year_date:
        if birthday_year[0] == "r":
            # 获取农历明年生日的月和日
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day


def get_ciba():
    url = "http://open.iciba.com/dsapi/"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    r = get(url, headers=headers)
    note_en = r.json()["content"]
    note_ch = r.json()["note"]
    return note_ch, note_en


def send_message(to_user, access_token, city_name, weather, max_temperature, min_temperature, note_ch, note_en, words):
    url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}".format(access_token)
    week_list = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    year = localtime().tm_year
    month = localtime().tm_mon
    day = localtime().tm_mday
    today = datetime.date(datetime(year=year, month=month, day=day))
    week = week_list[today.isoweekday() % 7]
    # 获取在一起的日子的日期格式
    love_year = int(config["love_date"].split("-")[0])
    love_month = int(config["love_date"].split("-")[1])
    love_day = int(config["love_date"].split("-")[2])
    love_date = date(love_year, love_month, love_day)
    # 获取在一起的日期差
    love_days = str(today.__sub__(love_date)).split(" ")[0]
    # 获取所有生日数据
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(today, week),
                "color": get_color()
            },
            "city": {
                "value": city_name,
                "color": get_color()
            },
            "weather": {
                "value": weather,
                "color": get_color()
            },
            "min_temperature": {
                "value": min_temperature,
                "color": get_color()
            },
            "max_temperature": {
                "value": max_temperature,
                "color": get_color()
            },
            "love_day": {
                "value": love_days,
                "color": get_color()
            },
            "note_en": {
                "value": note_en,
                "color": get_color()
            },
            "note_ch": {
                "value": note_ch,
                "color": get_color()
            },
            "words": {
                "value": words,
                "color": get_color()
            }
        }
    }
    for key, value in birthdays.items():
        # 获取距离下次生日的时间
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = "今天{}生日哦，{}生日快乐呀🌈！".format(value["name"], value["name"])
        else:
            birthday_data = "距离{}的生日还有{}天呀♥".format(value["name"], birth_day)
        # 将生日数据插入data
        data["data"][key] = {"value": birthday_data, "color": get_color()}


    yin = ['多云', '阴', '多云转阴']
    yu = ['小雨', '小雨转多云', '阴转小雨', '小雨转中雨', '中雨']
    if weather in yin:
        data["data"]["note"] = {"value": '今天是阴天(｡･∀･)ﾉﾞ', "color": get_color()}
        if int(min_temperature.split("℃")[0]) < 10:
            data["data"]["note"] = {"value": '今天最低气温小于10℃，宝贝注意保暖呀', "color": get_color()}
    elif weather in yu:
        data["data"]["note"] = {"value": '今天可能有雨，宝贝记得带伞呀(｡･∀･)ﾉﾞ', "color": get_color()}
    elif weather == "晴":
        data["data"]["note"] = {"value": '今天是晴天呀(●ˇ∀ˇ●)✌', "color": get_color()}
    else:
        try:
            data["data"].pop("note")
        except:
            pass

    if week == week_list[5]:
        print('week4')
        data["data"]['friday'] = {"value": "宝贝明天可以睡懒觉了哦(●ˇ∀ˇ●)", "color": get_color()}
    elif week == week_list[0]:
        data["data"]['friday'] = {"value": "到了周末了呀，宝贝好好放松哦O(∩_∩)O", "color": get_color()}
    elif week == week_list[6]:
        data["data"]['friday'] = {"value": "到了周末了呀，宝贝好好放松哦O(∩_∩)O", "color": get_color()}
    else:
        t = 6 - today.isoweekday() % 7
        data["data"]['friday'] = {"value": "距离周末还有" + str(t) + "天,加油呀ε=( o｀ω′)ノ 宝贝", "color": get_color()}

    dayima_pre = [2, 3]
    dayima = [4, 5, 6]
    if day in dayima_pre:
        data["data"]['dayima'] = {"value": "宝贝注意不要吃凉的呀，亲戚快要来啦, 提前准备好暖宝宝呀", "color": get_color()}
    elif day in dayima:
        data["data"]['dayima'] = {"value": "抱抱宝贝👶，宝贝受苦啦 好好暖暖肚肚啊", "color": get_color()}
    else:
        try:
            data["data"].pop('dayima')
        except:
            pass

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    response = post(url, headers=headers, json=data).json()
    if response["errcode"] == 40037:
        print("推送消息失败，请检查模板id是否正确")
    elif response["errcode"] == 40036:
        print("推送消息失败，请检查模板id是否为空")
    elif response["errcode"] == 40003:
        print("推送消息失败，请检查微信号是否正确")
    elif response["errcode"] == 0:
        print("推送消息成功")
    else:
        print(response)


def get_text():
    txt = open('words.txt', 'rb')
    data = txt.read().decode('utf-8')
    txt.close()
    n = data.count('\n')
    i = random.randint(1, (n + 1))
    text = linecache.getline(r'words.txt', i)
    return text


if __name__ == "__main__":

    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except FileNotFoundError:
        print("推送消息失败，请检查config.txt文件是否与程序位于同一路径")
        os.system("pause")
        sys.exit(1)
    except SyntaxError:
        print("推送消息失败，请检查配置文件格式是否正确")
        os.system("pause")
        sys.exit(1)

    accessToken = get_access_token()

    words = get_text()
    users = config["user"]
    province, city = config["province"], config["city"]
    weather, max_temperature, min_temperature = get_weather(province, city)
    note_ch, note_en = get_ciba()
    for user in users:
        send_message(user, accessToken, city, weather, max_temperature, min_temperature, note_ch, note_en, words)
    os.system("pause")




