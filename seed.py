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
        # Removed dummy transactions to start from scratch.
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
