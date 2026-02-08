from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product, Cart

def register_routes(app):

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

            user = User(
                name=name,
                email=email,
                password=generate_password_hash(password)
            )

            db.session.add(user)
            db.session.commit()
            return redirect(url_for("login"))

        return render_template("home.html")


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user = User.query.filter_by(
                email=request.form.get("loginmailid")
            ).first()

            if user and check_password_hash(
                user.password,
                request.form.get("loginpassword")
            ):
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

        item = Cart.query.filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()

        if item:
            item.quantity += 1
        else:
            db.session.add(
                Cart(user_id=user_id, product_id=product_id)
            )

        db.session.commit()
        return redirect(url_for("cart"))


    @app.route('/cart')
    def cart():
        if 'user_id' not in session:
            return redirect(url_for("login"))

        cart_items = Cart.query.filter_by(
            user_id=session["user_id"]
        ).all()

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
