# Imported Necessary Libraries
from app import createApp, db  
from app.models import User

# Created App Instance
app = createApp()

# Create All Database Tables And Seed Default Users
with app.app_context():
    db.create_all()
    if User.query.count() == 0:
        admin = User(username='admin', email='admin@example.com')
        admin.setPassword('admin123')
        user1 = User(username='user1', email='user1@example.com')
        user1.setPassword('letmein')
        user2 = User(username='user2', email='user2@example.com')
        user2.setPassword('welcome123')
        db.session.add_all([admin, user1, user2])
        db.session.commit()
        print("Seeded Default Users: Admin, User1, User2")

# Run The Application
if __name__ == '__main__':
    app.run(debug=True)
