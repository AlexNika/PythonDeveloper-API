import os

from PIL import Image
from flask import Flask, render_template, request, flash
from flask import redirect, url_for, send_from_directory, session
from flask_caching import Cache
from wordcloud import WordCloud

import modules.api_library as APILib
import modules.sqlalchemy_library as SQLLib
from modules.variables import background_color

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


@app.route('/images/')
def images():
    return send_from_directory(os.path.join(app.root_path, 'images'), 'key_skills.png',
                               mimetype='image/png')


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
    session['VACANCY_NAME'] = 'Python developer'
    session['AREA_NAME'] = 'Москва'
    session['HHRU_CHECKED'] = 'on'
    session['SJRU_CHECKED'] = None
    session['FILENAME'] = ''
    session['cloud_skills'] = None
    if request.form['vacancy_name']:
        session['VACANCY_NAME'] = request.form['vacancy_name']
    if request.form['area_name']:
        session['AREA_NAME'] = request.form['area_name']
    session['HHRU_CHECKED'] = request.form.get('hhru')
    session['SJRU_CHECKED'] = request.form.get('sjru')
    if session['HHRU_CHECKED'] is None and session['SJRU_CHECKED'] is None:
        session['HHRU_CHECKED'] = 'on'
    _cloud_skills = {}
    session['VACANCY_NAME'] = session['VACANCY_NAME'].lower()
    if session['HHRU_CHECKED'] == 'on':
        _area_id = SQLLib.area_dbrw(session['AREA_NAME'])
        if not _area_id:
            flash(f'В базе HH.RU регион "{session["AREA_NAME"]}" не найден! Попробуйте ввести другой регион.', 'error')
            return redirect(url_for('result'), code=302)
        _result, _request_id = SQLLib.request_dbrw(session['VACANCY_NAME'], _area_id)
        if not _result:
            _vacancy_info, _cloud_skills = APILib.process_hhru(session['VACANCY_NAME'], session['AREA_NAME'], _area_id)
            if _cloud_skills:
                _vacancy_id = SQLLib.vacancy_info_dbw(_request_id, _vacancy_info)
                SQLLib.key_skills_dbw(_vacancy_id, _cloud_skills)
        else:
            _vacancy_id = SQLLib.vacancy_info_dbr(_request_id)
            if _vacancy_id:
                _cloud_skills = SQLLib.key_skills_dbr(_vacancy_id)
    if _cloud_skills:
        session['cloud_skills'] = _cloud_skills
    else:
        flash(f'В регионе "{session["AREA_NAME"]}" вакансий "{session["VACANCY_NAME"]}" не найдено!', 'error')
    return redirect(url_for('result'), code=302)


@app.route('/result/')
def result():
    with app.app_context():
        cache.clear()
    cloud = WordCloud(background_color=background_color, width=600, max_words=200,
                      ranks_only=True, stopwords=set())
    _filename = 'key_skills.png'
    _image_folder = 'images'
    _fileurl = url_for('images', filename=_filename)
    _filename = f'{os.path.join(app.root_path, _image_folder, _filename)}'
    if os.path.exists(_filename):
        os.remove(_filename)
    try:
        if session.get('cloud_skills', None):
            cloud.generate_from_frequencies(session.get('cloud_skills', None))
            _cloud_skills_array = cloud.to_array()
            image = Image.fromarray(_cloud_skills_array)
            image.save(_filename)
        else:
            return render_template('result.html')
    except AttributeError:
        return render_template('result.html')
    flash(f'Название вакансии - {session.get("VACANCY_NAME", None)}', 'input')
    flash(f'Регион поиска - {session.get("AREA_NAME", None)}', 'input')
    flash(f'Выбран сайт HEADHUNTER  - {"Да" if session.get("HHRU_CHECKED", None) == "on" else "Нет"}', 'input')
    flash(f'Выбран сайт SUPERJOB - {"Да" if session.get("SJRU_CHECKED", None) == "on" else "Нет"}', 'input')
    return render_template('result.html', filename=_fileurl)


if __name__ == "__main__":
    app.debug = True
    app.config['SECRET_KEY'] = 'a really really really really long secret key'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run()


