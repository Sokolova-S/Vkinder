import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session
from config import db_url_object


metadata = MetaData()
Base = declarative_base()


class Viewed(Base):
    # Связь с БД

    __tablename__ = "viewed"
    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)


def add_user(profile_id, worksheet_id):
    # Добавление пользователя в БД

    engine = create_engine(db_url_object)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        to_bd = Viewed(profile_id=profile_id, worksheet_id=worksheet_id)
        session.add(to_bd)
        session.commit()
    return "Успешно добавлен в БД"


def delete_user_data(profile_id):
    # Удаление данных пользователя из бд

    engine = create_engine(db_url_object)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.query(Viewed).filter(
            Viewed.profile_id == profile_id
        ).delete(synchronize_session='fetch')
        session.commit()
    return "Данные удалены"


def check_user(profile_id, worksheet_id):
    # Извлечение записей из БД

    engine = create_engine(db_url_object)
    with Session(engine) as session:
        from_bd = session.query(sq.text(Viewed.__tablename__)).filter(
            Viewed.worksheet_id == worksheet_id,
            Viewed.profile_id == profile_id
        ).first()
        return False if from_bd else True


if __name__ == '__main__':
    engine = create_engine(db_url_object)
    Base.metadata.create_all(engine)
    # add_user(engine, 2113, 124512)
    # res = check_user(engine, 2113, 1245121)
    # print(res)

