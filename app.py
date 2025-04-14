from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///links.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '3d6ebe75d9755de59c71c7b2533309dbc627da7b3cc1af5b5256375a6743f6b4'  # Change this later
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    links = Link.query.filter_by(user_id=current_user.id).all() if current_user.is_authenticated else []
    return render_template('index.html', links=links, query='')

@app.route('/save', methods=['POST'])
@login_required
def save_link():
    url = request.form['url']
    title = request.form['title']
    tags = request.form['tags']
    new_link = Link(url=url, title=title, tags=tags, user_id=current_user.id)
    db.session.add(new_link)
    db.session.commit()
    return render_template('index.html', links=Link.query.filter_by(user_id=current_user.id).all(), query='', message='Link saved!')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    if current_user.is_authenticated:
        if query:
            links = Link.query.filter(
                (Link.title.ilike(f'%{query}%')) |
                (Link.tags.ilike(f'%{query}%')),
                Link.user_id == current_user.id
            ).all()
        else:
            links = Link.query.filter_by(user_id=current_user.id).all()
    else:
        links = []
    return render_template('index.html', links=links, query=query)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', message='Email already exists')
        new_user = User(email=email, password=password)  # Plain password for now
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:  # Plain password check for now
            login_user(user)
            return redirect(url_for('home'))
        return render_template('login.html', message='Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)