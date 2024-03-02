from flask import Flask, render_template, request
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import telegram
from telegram.ext import Updater, CommandHandler

app = Flask(__name__)
bot_token = "your token"

def sanitize_filename(filename):

    return "".join([c for c in filename if c not in ('/', '\\')])

def take_screenshot(movie_name, flask_url):
    driver_path = "C:\\Users\\Mohamad\\Downloads\\Compressed\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    s = Service(driver_path)
    driver = webdriver.Chrome(service=s, options=chrome_options)
    driver.get(flask_url)
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "targetDiv")))
    div_element = driver.find_element(By.ID, "targetDiv")
    location = div_element.location
    size = div_element.size
    driver.save_screenshot('full_screenshot.png')
    driver.quit()
    img = Image.open('full_screenshot.png')
    left = location['x']
    top = location['y']
    right = left + size['width']
    bottom = top + size['height']
    crop_box = (left, top, right, bottom)
    cropped_img = img.crop(crop_box)
    sanitized_movie_name = sanitize_filename(movie_name)
    cropped_img_path = f'cropped_screenshot_{sanitized_movie_name}.png'
    cropped_img.save(cropped_img_path)
    return cropped_img_path

def send_cropped_screenshot(cropped_img_path, bot_token, chat_id):
    bot = telegram.Bot(token=bot_token)
    with open(cropped_img_path, 'rb') as file:
        bot.send_photo(chat_id=chat_id, photo=file)

@app.route('/')
def welcome():
    return "Welcome to the Movie Bot! Send a movie name to generate a movie card."

@app.route('/make_card')
def make_card():
    movie_name = request.args.get('movie_name')
    url = f'https://api.themoviedb.org/3/search/movie?api_key=<YOURAPI>&query={movie_name}'
    headers = {
        'Authorization': 'Bearer ',
        'Accept': 'application/json',
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    if data['results']:
        movie_data = data['results'][0]
    else:
        movie_data = None
    return render_template('tmdb.html', data=movie_data)

def handle_movie_command(update, context):
    message = update.message
    text = message.text
    movie_name = text.replace('/movie', '').strip()
    context.bot.send_message(chat_id=message.chat_id, text='Generating movie card...')
    flask_base_url = 'http://127.0.0.1:5000/'
    flask_url = f'{flask_base_url}/make_card?movie_name={movie_name}'
    cropped_img_path = take_screenshot(movie_name, flask_url)
    send_cropped_screenshot(cropped_img_path, bot_token, message.chat_id)
    context.bot.send_message(chat_id=message.chat_id, text='Movie card generated and sent!')

if __name__ == '__main__':

    try:
        updater = Updater(token=bot_token, use_context=True)
        dispatcher = updater.dispatcher
        movie_command_handler = CommandHandler('movie', handle_movie_command)
        dispatcher.add_handler(movie_command_handler)
        updater.start_polling()
        app.run(debug=True, host="127.0.0.1", port=5000)
    except Exception as e:
        print(f"Error starting bot: {e}")