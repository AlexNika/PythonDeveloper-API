from datetime import datetime

import HHSQLModel
from modules.api_library import get_area


def area_dbrw(_area):
    result = HHSQLModel.db_session.query(HHSQLModel.Area).filter(HHSQLModel.Area.area_name_fld == _area).first()
    if not result:
        _area_id = get_area(_area)
        if _area_id:
            result = HHSQLModel.Area(_area_id, _area)
            HHSQLModel.db_session.add(result)
            HHSQLModel.db_session.commit()
            return _area_id
        else:
            return None
    else:
        return result.areacode_fld


def request_dbrw(_vacancy, _area_id):
    result = HHSQLModel.db_session.query(HHSQLModel.Request).filter(
        HHSQLModel.Request.re_vacancy_fld == _vacancy, HHSQLModel.Request.re_area_id == _area_id).first()
    if not result:
        current_time = datetime.now()
        result = HHSQLModel.Request(_area_id, _vacancy, current_time)
        HHSQLModel.db_session.add(result)
        HHSQLModel.db_session.commit()
        request_id = result.re_id
        result = None
    else:
        request_id = result.re_id
        request_time = datetime.strptime(str(result.re_datetime_fld), '%Y-%m-%d %H:%M:%S.%f')
        current_time = datetime.now()
        delta = current_time - request_time
        if delta.days >= 1:
            result.re_datetime_fld = current_time
            HHSQLModel.db_session.commit()
            result = None
    return result, request_id


def vacancy_info_dbw(request_id, vacancy_info):
    result = HHSQLModel.db_session.query(HHSQLModel.VacancyInfo).filter(
        HHSQLModel.VacancyInfo.request_id == request_id).first()
    if not result:
        result = HHSQLModel.VacancyInfo(request_id, vacancy_info['2.count'], vacancy_info['3.avg_min_salary'],
                                        vacancy_info['4.avg_max_salary'], vacancy_info['5.skills_quantity'])
        HHSQLModel.db_session.add(result)
        HHSQLModel.db_session.commit()
        vacancy_id = result.vacancy_id
    else:
        vacancy_id = result.vacancy_id
        result.vacancies_count_fld = vacancy_info['2.count']
        result.avg_min_salary_fld = vacancy_info['3.avg_min_salary']
        result.avg_max_salary_fld = vacancy_info['4.avg_max_salary']
        result.skills_quantity_fld = vacancy_info['5.skills_quantity']
        HHSQLModel.db_session.commit()
    return vacancy_id


def vacancy_info_dbr(request_id):
    result = HHSQLModel.db_session.query(HHSQLModel.VacancyInfo).filter(
        HHSQLModel.VacancyInfo.request_id == request_id).first()
    if result:
        vacancy_id = result.vacancy_id
    else:
        vacancy_id = None
    return vacancy_id


def key_skills_dbw(vacancy_id, cloud_skills):
    result = HHSQLModel.db_session.query(HHSQLModel.KeySkills).filter(
        HHSQLModel.KeySkills.vacancy_id == vacancy_id).all()
    if not result:
        for skill in cloud_skills:
            result = HHSQLModel.KeySkills(vacancy_id, skill, cloud_skills[skill])
            HHSQLModel.db_session.add(result)
        HHSQLModel.db_session.commit()
    else:
        HHSQLModel.db_session.query(HHSQLModel.KeySkills).filter(
            HHSQLModel.KeySkills.vacancy_id == vacancy_id).delete()
        HHSQLModel.db_session.commit()
        for skill in cloud_skills:
            result = HHSQLModel.KeySkills(vacancy_id, skill, cloud_skills[skill])
            HHSQLModel.db_session.add(result)
        HHSQLModel.db_session.commit()
    return result


def key_skills_dbr(vacancy_id):
    cloud_skills = {}
    result = HHSQLModel.db_session.query(HHSQLModel.KeySkills).filter(
        HHSQLModel.KeySkills.vacancy_id == vacancy_id).all()
    for r in result:
        cloud_skills[result.key_skill_fld] = result.skill_quantity_fld
    return cloud_skills


