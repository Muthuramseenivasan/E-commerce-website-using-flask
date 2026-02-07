from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Mysecret123key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    items = db.relationship('Product', backref='owned_user', lazy=True)
    cart_items = db.relationship('Cart', backref='user', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(50), nullable=False,unique=True)
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(100), nullable=False)

    owner = db.Column(db.Integer, db.ForeignKey('user.id'))


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id'),
        nullable=False
    )

    quantity = db.Column(db.Integer, default=1)

    product = db.relationship('Product')


with app.app_context():
    db.create_all()


@app.route("/", methods=['GET', 'POST'])
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get("name")
        email = request.form.get("mailid")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not email.endswith("@gmail.com"):
            return "Email must end with @gmail.com"

        if password != confirm_password:
            return "Passwords do not match"

        if User.query.filter_by(email=email).first():
            return "Email already registered"

        hashed_password = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template("home.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("loginmailid")
        password = request.form.get("loginpassword")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("products"))

        return "Invalid email or password"

    return render_template("home.html")


@app.route("/products")
def products():
    if "user_id" not in session:
        return redirect(url_for("login"))

    products = Product.query.all()
    return render_template("products.html", products=products)


@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for("login"))

    user_id = session['user_id']

    cart_item = Cart.query.filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        new_item = Cart(
            user_id=user_id,
            product_id=product_id,
            quantity=1
        )
        db.session.add(new_item)

    db.session.commit()
    return redirect(url_for('cart'))


@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    grand_total = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    return render_template(
        "cart.html",
        cart_items=cart_items,
        grand_total=grand_total
    )


@app.route("/increase/<int:cart_id>")
def increase_quantity(cart_id):
    item = Cart.query.get_or_404(cart_id)
    item.quantity += 1
    db.session.commit()
    return redirect(url_for("cart"))


@app.route("/decrease/<int:cart_id>")
def decrease_quantity(cart_id):
    item = Cart.query.get_or_404(cart_id)
    if item.quantity > 1:
        item.quantity -= 1
        db.session.commit()
    return redirect(url_for("cart"))


@app.route("/remove-from-cart/<int:cart_id>")
def remove_from_cart(cart_id):
    item = Cart.query.get_or_404(cart_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("cart"))


@app.route('/logout')
def logout():
    session.clear()
    return render_template("logout.html")

if __name__ == "__main__":
    app.run(debug=True)
