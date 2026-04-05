"""Seed the database with demo data."""
from app import app, db
from models import User, Category, Transaction
from datetime import date, datetime


def seed():
    with app.app_context():
        db.create_all()

        # Check if already seeded
        if User.query.first():
            print("Database already seeded. Skipping.")
            return

        # --- Users ---
        admin = User(
            username='admin',
            email='admin@nextskills.com',
            full_name='Alex Mercer',
            role='Finance Admin'
        )
        admin.set_password('password123')

        sarah = User(
            username='sarah',
            email='sarah@nextskills.com',
            full_name='Sarah Jenkins',
            role='Head Administrator'
        )
        sarah.set_password('password123')

        david = User(
            username='david',
            email='david@nextskills.com',
            full_name='David Chen',
            role='Administrator'
        )
        david.set_password('password123')

        db.session.add_all([admin, sarah, david])
        db.session.flush()

        # --- Categories ---
        income_cats = [
            Category(name='Course Fees', icon='school', type='income'),
            Category(name='Corporate Training', icon='business', type='income'),
            Category(name='Consulting', icon='psychology', type='income'),
            Category(name='Sponsorships', icon='handshake', type='income'),
            Category(name='Merchandise', icon='storefront', type='income'),
        ]
        expense_cats = [
            Category(name='Office Supplies', icon='inventory_2', type='expense'),
            Category(name='Rent', icon='home_work', type='expense'),
            Category(name='Marketing', icon='campaign', type='expense'),
            Category(name='Salaries', icon='groups', type='expense'),
            Category(name='Utility', icon='bolt', type='expense'),
            Category(name='Infrastructure', icon='cloud', type='expense'),
        ]
        db.session.add_all(income_cats + expense_cats)
        db.session.flush()

        # --- Transactions ---
        transactions = [
            Transaction(
                type='income', amount=12400.00,
                date=date(2024, 10, 24),
                category_name='Course Fees',
                description='Tuition Payment - Batch A',
                entity_name='Batch A Students',
                admin_id=admin.id
            ),
            Transaction(
                type='expense', amount=1250.40,
                date=date(2024, 10, 22),
                category_name='Infrastructure',
                description='AWS Cloud Hosting',
                entity_name='Amazon Web Services',
                admin_id=sarah.id
            ),
            Transaction(
                type='expense', amount=3500.00,
                date=date(2024, 10, 21),
                category_name='Marketing',
                description='Marketing Campaign - Q4',
                entity_name='Digital Ads Agency',
                admin_id=admin.id
            ),
            Transaction(
                type='income', amount=8900.00,
                date=date(2024, 10, 20),
                category_name='Corporate Training',
                description='Corporate Training Contract',
                entity_name='TechCorp Industries',
                admin_id=david.id
            ),
            Transaction(
                type='income', amount=5200.00,
                date=date(2024, 10, 18),
                category_name='Consulting',
                description='Strategic Consulting - FinTech Startup',
                entity_name='PayStream Inc.',
                admin_id=admin.id
            ),
            Transaction(
                type='expense', amount=8500.00,
                date=date(2024, 10, 15),
                category_name='Salaries',
                description='Instructor Salaries - October',
                entity_name='Payroll',
                admin_id=sarah.id
            ),
            Transaction(
                type='income', amount=15800.00,
                date=date(2024, 10, 12),
                category_name='Course Fees',
                description='Advanced Python Bootcamp Registration',
                entity_name='Online Students',
                admin_id=admin.id
            ),
            Transaction(
                type='expense', amount=4200.00,
                date=date(2024, 10, 10),
                category_name='Rent',
                description='Office Space Rental - October',
                entity_name='WeWork',
                admin_id=sarah.id
            ),
            Transaction(
                type='expense', amount=970.10,
                date=date(2024, 10, 8),
                category_name='Utility',
                description='Internet & Phone Services',
                entity_name='Comcast Business',
                admin_id=david.id
            ),
        ]
        db.session.add_all(transactions)
        db.session.commit()

        print("Database seeded successfully!")
        print(f"  Users: {User.query.count()}")
        print(f"  Categories: {Category.query.count()}")
        print(f"  Transactions: {Transaction.query.count()}")
        print()
        print("Login credentials:")
        print("  Email: admin@nextskills.com")
        print("  Password: password123")


if __name__ == '__main__':
    seed()
