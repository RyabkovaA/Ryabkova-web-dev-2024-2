from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from models import db, Course, Category, User, Image, Review
from hashlib import md5
from werkzeug.utils import secure_filename
import os

bp = Blueprint('courses', __name__, url_prefix='/courses')

COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]
SCORE_NAMES = ['ужасно', 'плохо', 'неудовлетворительно', 'удовлетворительно', 'хорошо', 'отлично']


def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

@bp.route('/')
def index():
    req = db.select(Course)
    if request.args.get('name'):
        req = req.filter(Course.name.ilike(f'%{request.args.get("name")}%'))

    if request.args.getlist('category_ids'):
        req = req.filter(Course.category_id.in_(request.args.getlist("category_ids")))

    pagination = db.paginate(req)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())

@bp.route('/new')
@login_required
# @can_user('create')
def new():
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()

    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)

@bp.route('/create', methods=['POST'])
@login_required
# @can_user('create')
def create():
    try:
        image_file = request.files['background_img']
        if image_file.filename:
            image_type = os.path.splitext(image_file.filename)[1]
            image = Image(
                file_name = secure_filename(image_file.filename), 
                mime_type = image_file.mimetype, 
                hash = md5(image_file.read()).hexdigest()
            )
            db.session.add(image)
            db.session.commit()
        else:
            raise IntegrityError
        
        course = Course(**params(), image_id=image.id)
        db.session.add(course)
        db.session.commit()

        image_file.seek(0)
        image_file.save(f'{current_app.config["UPLOAD_FOLDER"]}/{image.id}{image_type}')
    except IntegrityError:
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        flash(f'Не заполнены все поля для корректного отображения курса!', 'danger')

        return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course)
    
    flash(f'Курс был успешно добавлен!', 'success')
    return redirect(url_for('courses.index'))

@bp.route('/<int:course_id>')
def show(course_id):
    course = db.get_or_404(Course, course_id)

    user_review = None
    if current_user.is_authenticated:
        user_review  = db.session.execute(db.select(Review).filter_by(course_id=course_id, user_id=current_user.id)).scalars().first()

    query  = db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc()).limit(5)
    reviews = db.session.execute(query).scalars().all()

    if user_review:
        reviews = [review for review in reviews if review.user_id != current_user.id]

    return render_template('courses/show.html', course=course, reviews=reviews, score_names=SCORE_NAMES, user_review=user_review)


@bp.route('/<int:course_id>/add_review', methods=['GET', 'POST'])
@login_required
def add_review(course_id):
    course = db.get_or_404(Course, course_id)

    if request.method == 'GET':
        return render_template('courses/add_review.html', score_names=SCORE_NAMES, course=course)

    rating = request.form.get('rating')
    text = request.form.get('text')
    if not text:
        flash('Добавьте текст рецензии!', category="danger")
        return render_template('courses/add_review.html', score_names=SCORE_NAMES, course=course)
                               
    review = Review(rating=rating, text=text, course_id=course_id, user_id=current_user.id)
    db.session.add(review)
    
    course.rating_sum += int(rating)
    course.rating_count += 1
    db.session.commit()
    
    flash('Ваша рецензия успешно добавлена!', 'success')
    return redirect(url_for('courses.show', course_id=course_id))

    # course = db.get_or_404(Course, course_id)

    # if request.method == 'POST':
    #     rating = request.form.get('rating')
    #     text = request.form.get('text')
    #     if text == None:
    #         flash('Добавьте текст рецензии!', category="danger")
    #         return render_template('courses/add_review.html', score_names=SCORE_NAMES, course=course)
                                
    #     review = Review(rating=rating, text=text, course_id=course_id, user_id=current_user.id)
    #     db.session.add(review)
        
    #     course.rating_sum += int(rating)
    #     course.rating_count += 1
    #     db.session.commit()
        
    #     flash('Ваша рецензия успешно добавлена!', 'success')
    #     return redirect(url_for('courses.show', course_id=course_id))
    
    # return render_template('courses/add_review.html', score_names=SCORE_NAMES, course=course)


# @bp.route('/<int:course_id>/reviews')
# def reviews(course_id):
#     course = db.get_or_404(Course, course_id)
#     sort_order = request.args.get('sort', 'newest')

#     if sort_order == 'positive':
#         reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.rating.desc())).scalars()

#     elif sort_order == 'negative':
#         reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.rating.asc())).scalars()

#     else:
#         reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())).scalars()

#     pagination = db.paginate(reviews, per_page=5)
#     reviews = pagination.items

#     return render_template('courses/reviews.html', 
#                            course=course,
#                            reviews=reviews,
#                            sort_order=sort_order, 
#                            pagination=pagination)


@bp.route('/<int:course_id>/reviews')
def reviews(course_id):
    course = db.get_or_404(Course, course_id)
    sort_order = request.args.get('sort', 'newest')

    if sort_order == 'positive':
        reviews = db.select(Review).filter_by(course_id=course_id).order_by(Review.rating.desc())

    elif sort_order == 'negative':
        reviews = db.select(Review).filter_by(course_id=course_id).order_by(Review.rating.asc())

    else:
        reviews = db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())

    pagination = db.paginate(reviews, per_page=5)
    reviews = pagination.items

    return render_template('courses/reviews.html', 
                           course=course,
                           reviews=reviews,
                           sort_order=sort_order, 
                           pagination=pagination, score_names=SCORE_NAMES)

# @bp.route('/<int:course_id>/reviews')
# def reviews(course_id):
#     course = db.get_or_404(Course, course_id)
#     sort_order = request.args.get('sort', 'newest')
#     page = request.args.get('page', 1, type=int)
#     per_page = 5

#     if sort_order == 'positive':
#         reviews_query = db.select(Review).filter_by(course_id=course_id).order_by(Review.rating.desc())
#     elif sort_order == 'negative':
#         reviews_query = db.select(Review).filter_by(course_id=course_id).order_by(Review.rating.asc())
#     else:
#         reviews_query = db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())

#     reviews_query = reviews_query.limit(per_page).offset((page - 1) * per_page)
#     reviews = db.session.execute(reviews_query).scalars().all()

#     total_reviews = db.session.execute(db.select(sa.func.count()).select_from(Review).filter_by(course_id=course_id)).scalar()
#     pagination = {
#         'page': page,
#         'per_page': per_page,
#         'total': total_reviews
#     }

#     return render_template('courses/reviews.html', 
#                            course=course,
#                            reviews=reviews,
#                            sort_order=sort_order, 
#                            pagination=pagination)