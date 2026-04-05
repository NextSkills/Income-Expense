from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from config import Config
from models import db, User, Transaction, Category
from datetime import datetime, date

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
csrf = CSRFProtect(app)

app.config['SESSION_SQLALCHEMY'] = db
Session(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'Finance Admin'

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return redirect(url_for('dashboard'))

class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'Finance Admin'

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))
        return redirect(url_for('dashboard'))

admin = Admin(app, name='Fiscal Architect DB', index_view=SecureAdminIndexView())
admin.add_view(SecureModelView(User, db.session))
admin.add_view(SecureModelView(Transaction, db.session))
admin.add_view(SecureModelView(Category, db.session))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        user = User.query.filter(
            (User.email == email) | (User.username == email)
        ).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    transactions = Transaction.query.order_by(Transaction.date.desc()).limit(10).all()
    total_income = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(
        Transaction.type == 'income'
    ).scalar()
    total_expense = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(
        Transaction.type == 'expense'
    ).scalar()
    balance = total_income - total_expense
    net_savings = total_income - total_expense
    goal = 65000.0
    goal_pct = min(int((net_savings / goal) * 100), 100) if goal > 0 else 0

    # Category breakdown for pie chart
    expense_cats = db.session.query(
        Transaction.category_name,
        db.func.sum(Transaction.amount)
    ).filter(Transaction.type == 'expense').group_by(Transaction.category_name).all()
    cat_total = sum(c[1] for c in expense_cats) if expense_cats else 1
    categories_data = [
        {'name': c[0] or 'Other', 'amount': c[1], 'pct': int((c[1] / cat_total) * 100)}
        for c in expense_cats
    ]

    return render_template('dashboard.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        net_savings=net_savings,
        goal_pct=goal_pct,
        categories_data=categories_data
    )


@app.route('/income/add', methods=['GET', 'POST'])
@login_required
def add_income():
    categories = Category.query.filter_by(type='income').all()
    if request.method == 'POST':
        txn = Transaction(
            type='income',
            amount=float(request.form.get('amount', 0)),
            date=datetime.strptime(request.form.get('date', ''), '%Y-%m-%d').date() if request.form.get('date') else date.today(),
            category_name=request.form.get('category', ''),
            entity_name=request.form.get('received_from', ''),
            entity_contact=request.form.get('payer_details', ''),
            description=request.form.get('description', ''),
            admin_id=current_user.id
        )
        db.session.add(txn)
        db.session.commit()
        flash('Income entry submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    last_entry = Transaction.query.filter_by(type='income').order_by(Transaction.created_at.desc()).first()
    total_collected = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(
        Transaction.type == 'income'
    ).scalar()
    goal = 65000.0
    goal_pct = min(int((total_collected / goal) * 100), 100) if goal > 0 else 0

    return render_template('add_income.html',
        categories=categories,
        last_entry=last_entry,
        total_collected=total_collected,
        goal=goal,
        goal_pct=goal_pct
    )


@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        txn = Transaction(
            type='expense',
            amount=float(request.form.get('amount', 0)),
            date=datetime.strptime(request.form.get('date', ''), '%Y-%m-%d').date() if request.form.get('date') else date.today(),
            category_name=request.form.get('category', ''),
            entity_name=request.form.get('paid_to', ''),
            entity_contact=request.form.get('contact_details', ''),
            description=request.form.get('description', ''),
            admin_id=current_user.id
        )
        db.session.add(txn)
        db.session.commit()
        flash('Expense entry submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('add_expense.html', users=users)


@app.route('/reports', methods=['GET'])
@login_required
def reports():
    return render_template('reports.html')


@app.route('/reports/generate', methods=['POST'])
@login_required
def generate_report():
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    include_inc = request.form.get('include_income') == 'yes'
    include_exp = request.form.get('include_expense') == 'yes'

    if not start_date_str or not end_date_str:
        flash('Please select both start and end dates.', 'error')
        return redirect(url_for('reports'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.', 'error')
        return redirect(url_for('reports'))

    types = []
    if include_inc: types.append('income')
    if include_exp: types.append('expense')

    if not types:
        flash('Please select at least one ledger type (Income or Expense).', 'error')
        return redirect(url_for('reports'))

    transactions = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.type.in_(types)
    ).order_by(Transaction.date.asc()).all()

    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    net_total = total_income - total_expense

    return render_template('report_print.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        net_total=net_total,
        start_date=start_date_str,
        end_date=end_date_str,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
