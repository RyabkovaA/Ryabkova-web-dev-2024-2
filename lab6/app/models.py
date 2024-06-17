import os
from typing import Optional, Union, List
from datetime import datetime
import sqlalchemy as sa
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Text, Integer, MetaData
from uuid import uuid4

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

db = SQLAlchemy(model_class=Base)

class Category(db.Model):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

    courses: Mapped[List['Course']] = relationship(back_populates="category")


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    courses: Mapped[List['Course']] = relationship(back_populates="author")
    reviews: Mapped[List['Review']] = relationship(back_populates="user")


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.middle_name or ""}'

class Course(db.Model):
    __tablename__ = 'courses'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    short_desc: Mapped[str] = mapped_column(String(512))
    full_desc: Mapped[str] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    rating_count: Mapped[float] = mapped_column(default=0)
    rating_sum: Mapped[int] = mapped_column(default=0)
    image_id: Mapped[str] = mapped_column(String(36), ForeignKey('images.id'))
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))

    author: Mapped['User'] = relationship(back_populates="courses")
    category: Mapped['Category'] = relationship(back_populates="courses")
    reviews: Mapped[List['Review']] = relationship(back_populates="course")


    @property
    def rating(self):
        try:
            return self.rating_sum / self.rating_count
        except ZeroDivisionError:
            return 0


class Image(db.Model):
    __tablename__ = 'images'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default = lambda: str(uuid4()))
    file_name: Mapped[str] = mapped_column(String(100))
    mime_type: Mapped[str] = mapped_column(String(100))
    hash: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    @property
    def storage_filename(self):
        return self.id + os.path.splitext(self.file_name)[-1]


class Review(db.Model):
    __tablename__ = 'reviews'
    id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[int] = mapped_column(default=0)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    course_id: Mapped[str] = mapped_column(ForeignKey('courses.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))

    user: Mapped['User'] = relationship(back_populates="reviews")
    course: Mapped['Course'] = relationship(back_populates="reviews")

