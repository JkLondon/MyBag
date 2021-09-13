from flask import Flask, request, abort
import requests
import urllib.parse
import json
from bs4 import BeautifulSoup
from selenium.webdriver import Firefox
from webdriver_manager.firefox import GeckoDriverManager

app = Flask(__name__)

app.add_url_rule("/soundcloud/user/", endpoint="get_user", methods=['GET', 'POST'])


def username_parse(text):
    text = str(text)
    point_first = text.find('com')
    point_first += 4
    point_last = point_first
    for i in range(point_first, len(text)):
        if text[i] == '"':
            point_last = i
            break
    return text[point_first:point_last]


def title_n_location_parse(text):
    text = str(text)
    point_first = text.find('=')
    point_first += 2
    point_last = point_first
    for i in range(point_first, len(text)):
        if text[i] == '"':
            point_last = i
            break
    return text[point_first:point_last]


def user_id_parse(text):
    text = str(text)
    point_first = text.find('users')
    point_first += 6
    point_last = point_first
    for i in range(point_first, len(text)):
        if text[i] == '"':
            point_last = i
            break
    return text[point_first:point_last]


def url_parse(text):
    text = str(text)
    point_first = text.find('url')
    point_first += 4
    point_last = point_first
    for i in range(point_first, len(text)):
        if text[i] == '&':
            point_last = i
            break
    return text[point_first:point_last]


def url_username_parse(text):
    text = text[::-1]
    point_last = text.find('/')
    text = text[:point_last]
    return text[::-1]


@app.endpoint("get_user")
def get_user():
    data = request.args
    users_id = data['query']
    response = requests.get('https://soundcloud.com/'+users_id).text
    soup = BeautifulSoup(response, features="html.parser")
    if soup.find("meta", content="noindex, nofollow") is None:
        username = username_parse(soup.find("meta", property="og:url"))
        title = title_n_location_parse(soup.find("meta", property="og:title"))
        location = title_n_location_parse(soup.find("meta", property="og:locality"))
        user_id = user_id_parse(soup.find("meta", property="al:ios:url"))
        browser = Firefox(executable_path=GeckoDriverManager().install())
        browser.get('https://soundcloud.com/'+users_id)
        browser.implicitly_wait(10)
        results = browser.find_elements_by_class_name("web-profiles__item")
        web_profiles = []
        for i in range(len(results)):
            link = url_parse(urllib.parse.unquote_plus(results[i].
                                                       find_element_by_class_name("web-profile").get_property("href")))
            social_profile = {"url": link, "network": results[i].text.lower(), "title": results[i].text}
            if social_profile["title"] == "WEBSITE":
                social_profile["username"] = ""
            else:
                social_profile["username"] = url_username_parse(link)
            web_profiles.append(social_profile)
        browser.close()
        results = {"id": user_id, "alias": username, "name": title, "country": location, "web_profiles": web_profiles}
        results = json.dumps(results)
        return results
    else:
        abort(404)


if __name__ == "__main__":
    app.run(debug=True)
