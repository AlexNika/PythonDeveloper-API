import os
from PIL import Image
from wordcloud import WordCloud
from modules.api_library import *
from flask import Flask, render_template, request, flash
from flask import redirect, url_for, send_from_directory
from flask_caching import Cache


VACANCY_NAME = 'Python developer'
AREA_NAME = 'Москва'
HHRU_CHECKED = 'on'
SJRU_CHECKED = None
FILENAME = None

cache = Cache(config={'CACHE_TYPE': 'null'})
app = Flask(__name__)
cache.init_app(app)


@app.after_request
def add_header(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/contacts/')
def contacts():
    return render_template('contacts.html')


@app.route('/queryform/', methods=['GET'])
def queryform_get():
    return render_template('queryform.html')


@app.route('/queryform/', methods=['POST'])
def queryform_post():
    global VACANCY_NAME
    global AREA_NAME
    global HHRU_CHECKED
    global SJRU_CHECKED
    global FILENAME
    FILENAME = ''
    if request.form['vacancy_name']:
        VACANCY_NAME = request.form['vacancy_name']
    if request.form['area_name']:
        AREA_NAME = request.form['area_name']
    HHRU_CHECKED = request.form.get('hhru')
    SJRU_CHECKED = request.form.get('sjru')
    if HHRU_CHECKED is None and SJRU_CHECKED is None:
        HHRU_CHECKED = 'on'
    _cloud_skills = {}
    if HHRU_CHECKED == 'on':
        _vacancy_info, _cloud_skills = process_hhru(VACANCY_NAME, AREA_NAME)
    if _cloud_skills:
        cloud = WordCloud(background_color=background_color, width=600, max_words=200, ranks_only=True, stopwords=set())
        cloud.generate_from_frequencies(_cloud_skills)
        FILENAME = 'key_skills.png'
        _cloud_skills_array = cloud.to_array()
        image = Image.fromarray(_cloud_skills_array)
        image.save(FILENAME)
        _filename = f'{os.path.join(app.root_path, "static")}\\images\\{FILENAME}'
        if os.path.exists(_filename):
            os.remove(_filename)
        os.rename(FILENAME, f'{os.path.join(app.root_path, "static")}\\images\\{FILENAME}')
    else:
        flash(f'В регионе "{AREA_NAME}" вакансий "{VACANCY_NAME}" не найдено!', 'error')
    return redirect(url_for('result'), code=302)


@app.route('/result/')
def result():
    with app.app_context():
        cache.clear()
    global FILENAME
    flash(f'Название вакансии - {VACANCY_NAME}', 'input')
    flash(f'Регион поиска - {AREA_NAME}', 'input')
    flash(f'Выбран сайт HEADHUNTER  - {"Да" if HHRU_CHECKED == "on" else "Нет"}', 'input')
    flash(f'Выбран сайт SUPERJOB - {"Да" if SJRU_CHECKED == "on" else "Нет"}', 'input')
    return render_template('result.html', filename=FILENAME)


if __name__ == "__main__":
    app.debug = True
    app.config['SECRET_KEY'] = 'a really really really really long secret key'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run()
