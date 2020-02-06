import os
import sqlite3
from datetime import datetime, timezone
from dateutil import *

from modules.variables import DB_FILENAME
from modules.api_library import get_area


def open_dbconnection(_filename):
    db_name = os.path.join(os.getcwd(), _filename)
    connector = sqlite3.connect(db_name)
    return connector


def close_dbconnection(_filename):
    open_dbconnection(_filename).close()


def area_dbrw(_area):
    connector = open_dbconnection(DB_FILENAME)
    cursor = connector.cursor()
    _sql = 'SELECT * FROM area_tbl WHERE areaname_fld=?'
    _query = (_area,)
    _result = cursor.execute(_sql, _query).fetchone()
    if not _result:
        _area_id = get_area(_area)
        if _area_id:
            _sql = 'INSERT INTO area_tbl (areacode_hh_fld, areaname_fld) VALUES (?, ?)'
            _query = (_area_id, _area)
            cursor.execute(_sql, _query)
            connector.commit()
            close_dbconnection(DB_FILENAME)
            return _area_id
        else:
            close_dbconnection(DB_FILENAME)
            return None
    else:
        close_dbconnection(DB_FILENAME)
        return _result[1]


def request_dbrw(_vacancy, _area_id):
    connector = open_dbconnection(DB_FILENAME)
    cursor = connector.cursor()
    _query = (_vacancy, _area_id)
    _sql = 'SELECT * FROM request_tbl WHERE re_vacancy_fld=? AND re_area_id=?'
    _result = cursor.execute(_sql, _query).fetchone()
    if not _result:
        _sql = 'INSERT INTO request_tbl (re_vacancy_fld, re_area_id) VALUES (?, ?)'
        cursor.execute(_sql, _query)
        connector.commit()
        _sql = 'SELECT re_id FROM request_tbl WHERE rowid=last_insert_rowid()'
        _result = cursor.execute(_sql).fetchone()
        _request_id = _result[0]
        _result = None
    else:
        _request_id = _result[0]
        utc_zone = tz.tzutc()
        request_time = datetime.strptime(_result[3], '%Y-%m-%d %H:%M:%S').replace(tzinfo=utc_zone)
        current_time = datetime.now(timezone.utc)
        delta = current_time - request_time
        if delta.days >= 1:
            _sql = 'UPDATE request_tbl SET re_datetime_fld=? WHERE re_id=?'
            _query = (datetime.strftime(current_time, '%Y-%m-%d %H:%M:%S'), _request_id)
            cursor.execute(_sql, _query)
            connector.commit()
            _result = None
    close_dbconnection(DB_FILENAME)
    return _result, _request_id


def vacancy_info_dbw(_request_id, _vacancy_info):
    connector = open_dbconnection(DB_FILENAME)
    cursor = connector.cursor()
    _sql = 'SELECT * FROM vacancy_info_tbl WHERE request_id=?'
    _query = (_request_id, )
    _result = cursor.execute(_sql, _query).fetchone()
    if not _result:
        _sql = 'INSERT INTO vacancy_info_tbl (request_id, vacancies_count_fld, avg_min_salary_fld, ' \
               'avg_max_salary_fld, skills_quantity_fld) VALUES (?, ?, ?, ?, ?)'
        _query = (_request_id, _vacancy_info['2.count'], _vacancy_info['3.avg_min_salary'],
                  _vacancy_info['4.avg_max_salary'], _vacancy_info['5.skills_quantity'])
        cursor.execute(_sql, _query)
        connector.commit()
        _sql = 'SELECT vacancy_id FROM vacancy_info_tbl WHERE rowid=last_insert_rowid()'
        _vacancy_id = cursor.execute(_sql).fetchone()
    else:
        _vacancy_id = _result
        _sql = 'UPDATE vacancy_info_tbl SET vacancies_count_fld=?, avg_min_salary_fld=?, ' \
               'avg_max_salary_fld=?, skills_quantity_fld=? WHERE vacancy_id=?'
        _query = (_vacancy_info['2.count'], _vacancy_info['3.avg_min_salary'],
                  _vacancy_info['4.avg_max_salary'], _vacancy_info['5.skills_quantity'],
                  _vacancy_id[0])
        cursor.execute(_sql, _query)
        connector.commit()
    close_dbconnection(DB_FILENAME)
    return _vacancy_id[0]


def vacancy_info_dbr(_request_id):
    connector = open_dbconnection(DB_FILENAME)
    cursor = connector.cursor()
    _sql = 'SELECT * FROM vacancy_info_tbl WHERE request_id=?'
    _query = (_request_id, )
    _result = cursor.execute(_sql, _query).fetchone()
    close_dbconnection(DB_FILENAME)
    if _result:
        _vacancy_id = _result[0]
    else:
        _vacancy_id = None
    return _vacancy_id


def key_skills_dbw(_vacancy_id, _cloud_skills):
    connector = open_dbconnection(DB_FILENAME)
    cursor = connector.cursor()
    _sql = 'SELECT * FROM key_skills_tbl WHERE vacancy_id=?'
    _query = (_vacancy_id, )
    _result = cursor.execute(_sql, _query).fetchall()
    if not _result:
        for skill in _cloud_skills:
            _sql = 'INSERT INTO key_skills_tbl (vacancy_id, key_skill_fld, skill_quantity_fld) VALUES (?, ?, ?)'
            _query = (_vacancy_id, skill, _cloud_skills[skill])
            cursor.execute(_sql, _query)
        connector.commit()
    else:
        _sql = 'DELETE FROM key_skills_tbl WHERE vacancy_id=?'
        _query = (_vacancy_id,)
        cursor.execute(_sql, _query)
        for skill in _cloud_skills:
            _sql = 'INSERT INTO key_skills_tbl (vacancy_id, key_skill_fld, skill_quantity_fld) VALUES (?, ?, ?)'
            _query = (_vacancy_id, skill, _cloud_skills[skill])
            cursor.execute(_sql, _query)
        connector.commit()
    close_dbconnection(DB_FILENAME)
    return _result


def key_skills_dbr(_vacancy_id):
    _cloud_skills = {}
    connector = open_dbconnection(DB_FILENAME)
    cursor = connector.cursor()
    _sql = 'SELECT * FROM key_skills_tbl WHERE vacancy_id=?'
    _query = (_vacancy_id, )
    _result = cursor.execute(_sql, _query).fetchall()
    close_dbconnection(DB_FILENAME)
    for r in _result:
        _cloud_skills[r[2]] = r[3]
    return _cloud_skills
