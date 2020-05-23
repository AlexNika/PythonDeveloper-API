from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///modules/ksc4alchemy.db3', echo=False)
Base = declarative_base()


class Area(Base):
    __tablename__ = 'area_tbl'
    area_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    areacode_fld = Column(Integer, unique=True)
    area_name_fld = Column(String, unique=True)

    def __init__(self, areacode_fld, area_name_fld):
        self.areacode_fld = areacode_fld
        self.area_name_fld = area_name_fld


class Request(Base):
    __tablename__ = 'request_tbl'
    re_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    re_area_id = Column(Integer, ForeignKey('area_tbl.area_id'), nullable=False)
    re_vacancy_fld = Column(String)
    re_datetime_fld = Column(String, unique=True)

    def __init__(self, re_area_id, re_vacancy_fld, re_datetime_fld):
        self.re_area_id = re_area_id
        self.re_vacancy_fld = re_vacancy_fld
        self.re_datetime_fld = re_datetime_fld


class VacancyInfo(Base):
    __tablename__ = 'vacancy_info_tbl'
    vacancy_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    request_id = Column(Integer, ForeignKey('request_tbl.re_id'), nullable=False)
    vacancies_count_fld = Column(Integer)
    avg_min_salary_fld = Column(Integer)
    avg_max_salary_fld = Column(Integer)
    skills_quantity_fld = Column(Integer)

    def __init__(self, request_id, vacancies_count_fld, avg_min_salary_fld,
                 avg_max_salary_fld, skills_quantity_fld):
        self.request_id = request_id
        self.vacancies_count_fld = vacancies_count_fld
        self.avg_min_salary_fld = avg_min_salary_fld
        self.avg_max_salary_fld = avg_max_salary_fld
        self.skills_quantity_fld = skills_quantity_fld


class KeySkills(Base):
    __tablename__ = 'key_skills_tbl'
    key_skills_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    vacancy_id = Column(Integer, ForeignKey('vacancy_info_tbl.vacancy_id'), nullable=False)
    key_skill_fld = Column(String)
    skill_quantity_fld = Column(Integer)

    def __init__(self, vacancy_id, key_skill_fld, skill_quantity_fld):
        self.vacancy_id = vacancy_id
        self.key_skill_fld = key_skill_fld
        self.skill_quantity_fld = skill_quantity_fld


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db_session = Session()
