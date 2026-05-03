from flask import Flask, render_template, redirect, url_for, flash, request
import os
from werkzeug.utils import secure_filename
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

admin = Admin(app, name='Next Skills Academy DB', index_view=SecureAdminIndexView())
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
        return redirect(url_for('add_income'))

    last_entry = Transaction.query.filter_by(type='income').order_by(Transaction.created_at.desc()).first()
    total_collected = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(
        Transaction.type == 'income'
    ).scalar()
    goal = 65000.0
    goal_pct = min(int((total_collected / goal) * 100), 100) if goal > 0 else 0

    # All income transactions for the display table
    income_transactions = Transaction.query.filter_by(type='income').order_by(Transaction.date.desc()).all()

    return render_template('add_income.html',
        categories=categories,
        last_entry=last_entry,
        total_collected=total_collected,
        goal=goal,
        goal_pct=goal_pct,
        income_transactions=income_transactions
    )


@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        # Handle File Upload
        receipt_path = None
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename != '':
                # Ensure upload directory exists
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                # Store relative path for web access
                receipt_path = os.path.join('uploads', 'receipts', filename).replace('\\', '/')

        txn = Transaction(
            type='expense',
            amount=float(request.form.get('amount', 0)),
            date=datetime.strptime(request.form.get('date', ''), '%Y-%m-%d').date() if request.form.get('date') else date.today(),
            category_name=request.form.get('category', ''),
            entity_name=request.form.get('paid_to', ''),
            entity_contact=request.form.get('contact_details', ''),
            description=request.form.get('description', ''),
            receipt_path=receipt_path,
            admin_id=current_user.id
        )
        db.session.add(txn)
        db.session.commit()
        flash('Expense entry submitted successfully!', 'success')
        return redirect(url_for('add_expense'))

    categories = Category.query.filter_by(type='expense').all()
    users = User.query.all()

    # All expense transactions for the display table
    expense_transactions = Transaction.query.filter_by(type='expense').order_by(Transaction.date.desc()).all()
    total_expense_amount = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(
        Transaction.type == 'expense'
    ).scalar()

    return render_template('add_expense.html',
        users=users,
        categories=categories,
        expense_transactions=expense_transactions,
        total_expense_amount=total_expense_amount
    )


@app.route('/expense/<int:txn_id>/edit', methods=['POST'])
@login_required
def edit_expense(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    if txn.type != 'expense':
        flash('Invalid transaction type.', 'error')
        return redirect(url_for('add_expense'))

    txn.amount = float(request.form.get('amount', txn.amount))
    txn.category_name = request.form.get('category', txn.category_name)
    txn.entity_name = request.form.get('entity_name', txn.entity_name)
    txn.entity_contact = request.form.get('entity_contact', txn.entity_contact)
    txn.description = request.form.get('description', txn.description)

    date_str = request.form.get('date', '')
    if date_str:
        try:
            txn.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Handle receipt replacement
    if 'receipt' in request.files:
        file = request.files['receipt']
        if file and file.filename != '':
            if txn.receipt_path:
                old_path = os.path.join('static', txn.receipt_path)
                if os.path.exists(old_path):
                    os.remove(old_path)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            txn.receipt_path = os.path.join('uploads', 'receipts', filename).replace('\\', '/')

    db.session.commit()
    flash(f'Expense #{txn.id} updated successfully.', 'success')
    return redirect(url_for('add_expense'))


@app.route('/expense/<int:txn_id>/delete', methods=['POST'])
@login_required
def delete_expense(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    if txn.type != 'expense':
        flash('Invalid transaction type.', 'error')
        return redirect(url_for('add_expense'))

    if txn.receipt_path:
        file_path = os.path.join('static', txn.receipt_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(txn)
    db.session.commit()
    flash('Expense deleted successfully.', 'success')
    return redirect(url_for('add_expense'))


@app.route('/income/<int:txn_id>/edit', methods=['POST'])
@login_required
def edit_income(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    if txn.type != 'income':
        flash('Invalid transaction type.', 'error')
        return redirect(url_for('add_income'))

    txn.amount = float(request.form.get('amount', txn.amount))
    txn.category_name = request.form.get('category', txn.category_name)
    txn.entity_name = request.form.get('entity_name', txn.entity_name)
    txn.entity_contact = request.form.get('entity_contact', txn.entity_contact)
    txn.description = request.form.get('description', txn.description)

    date_str = request.form.get('date', '')
    if date_str:
        try:
            txn.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    db.session.commit()
    flash(f'Income #{txn.id} updated successfully.', 'success')
    return redirect(url_for('add_income'))


@app.route('/income/<int:txn_id>/delete', methods=['POST'])
@login_required
def delete_income(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    if txn.type != 'income':
        flash('Invalid transaction type.', 'error')
        return redirect(url_for('add_income'))

    db.session.delete(txn)
    db.session.commit()
    flash('Income deleted successfully.', 'success')
    return redirect(url_for('add_income'))


@app.route('/admin/transactions')
@login_required
def manage_transactions():
    if current_user.role != 'Finance Admin':
        flash('You do not have permission to access that page.', 'error')
        return redirect(url_for('dashboard'))

    # Filters
    filter_type = request.args.get('type', 'all')
    filter_category = request.args.get('category', 'all')
    search_query = request.args.get('q', '').strip()

    query = Transaction.query

    if filter_type != 'all':
        query = query.filter(Transaction.type == filter_type)
    if filter_category != 'all':
        query = query.filter(Transaction.category_name == filter_category)
    if search_query:
        query = query.filter(
            db.or_(
                Transaction.description.ilike(f'%{search_query}%'),
                Transaction.entity_name.ilike(f'%{search_query}%'),
                Transaction.category_name.ilike(f'%{search_query}%')
            )
        )

    transactions = query.order_by(Transaction.date.desc()).all()

    # Get all unique categories for filter dropdown
    all_categories = db.session.query(Transaction.category_name).distinct().all()
    category_names = sorted([c[0] for c in all_categories if c[0]])

    # Stats
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')

    # All categories for edit modal
    income_categories = Category.query.filter_by(type='income').all()
    expense_categories = Category.query.filter_by(type='expense').all()

    return render_template('manage_transactions.html',
        transactions=transactions,
        filter_type=filter_type,
        filter_category=filter_category,
        search_query=search_query,
        category_names=category_names,
        total_income=total_income,
        total_expense=total_expense,
        income_categories=income_categories,
        expense_categories=expense_categories
    )


@app.route('/admin/transactions/<int:txn_id>/edit', methods=['POST'])
@login_required
def edit_transaction(txn_id):
    if current_user.role != 'Finance Admin':
        flash('You do not have permission to perform that action.', 'error')
        return redirect(url_for('dashboard'))

    txn = Transaction.query.get_or_404(txn_id)

    txn.type = request.form.get('type', txn.type)
    txn.amount = float(request.form.get('amount', txn.amount))
    txn.category_name = request.form.get('category', txn.category_name)
    txn.entity_name = request.form.get('entity_name', txn.entity_name)
    txn.entity_contact = request.form.get('entity_contact', txn.entity_contact)
    txn.description = request.form.get('description', txn.description)

    date_str = request.form.get('date', '')
    if date_str:
        try:
            txn.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Handle receipt replacement
    if 'receipt' in request.files:
        file = request.files['receipt']
        if file and file.filename != '':
            # Delete old receipt if exists
            if txn.receipt_path:
                old_path = os.path.join('static', txn.receipt_path)
                if os.path.exists(old_path):
                    os.remove(old_path)

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            txn.receipt_path = os.path.join('uploads', 'receipts', filename).replace('\\', '/')

    db.session.commit()
    flash(f'Transaction #{txn.id} updated successfully.', 'success')
    return redirect(url_for('manage_transactions'))


@app.route('/admin/transactions/<int:txn_id>/delete', methods=['POST'])
@login_required
def delete_transaction(txn_id):
    if current_user.role != 'Finance Admin':
        flash('You do not have permission to perform that action.', 'error')
        return redirect(url_for('dashboard'))

    txn = Transaction.query.get_or_404(txn_id)

    # Delete receipt file if exists
    if txn.receipt_path:
        file_path = os.path.join('static', txn.receipt_path)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(txn)
    db.session.commit()
    flash(f'Transaction deleted successfully.', 'success')
    return redirect(url_for('manage_transactions'))


@app.route('/add-admin', methods=['GET', 'POST'])
@login_required
def add_admin():
    if current_user.role != 'Finance Admin':
        flash('You do not have permission to access that page.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'Administrator')

        if not full_name or not email or not username or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('add_admin'))

        # Check for existing email/username
        existing_user = User.query.filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            flash('That email or username is already in use.', 'error')
            return redirect(url_for('add_admin'))

        new_user = User(
            full_name=full_name,
            email=email,
            username=username,
            role=role
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Administrator ({full_name}) created successfully.', 'success')
        return redirect(url_for('add_admin'))

    return render_template('add_admin.html')


@app.route('/add-category', methods=['GET', 'POST'])
@login_required
def add_category():
    if current_user.role != 'Finance Admin':
        flash('You do not have permission to access that page.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        type_val = request.form.get('type', 'expense').strip()
        icon = request.form.get('icon', '').strip()

        if not name or not type_val:
            flash('Category Name and Type are required.', 'error')
            return redirect(url_for('add_category'))
            
        if not icon:
            icon = 'category'

        # Check if category already exists
        existing_cat = Category.query.filter_by(name=name, type=type_val).first()
        if existing_cat:
            flash(f'The {type_val} category "{name}" already exists.', 'error')
            return redirect(url_for('add_category'))

        new_cat = Category(
            name=name,
            type=type_val,
            icon=icon
        )

        db.session.add(new_cat)
        db.session.commit()
        
        flash(f'Category "{name}" added successfully.', 'success')
        return redirect(url_for('add_category'))

    return render_template('add_category.html')


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not full_name or not email or not username:
            flash('Full Name, Email, and Username are required.', 'error')
            return redirect(url_for('settings'))

        # Check for existing email/username taken by OTHER users
        existing_user = User.query.filter(
            ((User.email == email) | (User.username == username)) & (User.id != current_user.id)
        ).first()

        if existing_user:
            flash('That email or username is already in use by another account.', 'error')
            return redirect(url_for('settings'))

        current_user.full_name = full_name
        current_user.email = email
        current_user.username = username

        if password:
            current_user.set_password(password)

        db.session.commit()
        flash('Your settings have been updated successfully.', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html')


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
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)
