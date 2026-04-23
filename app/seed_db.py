from app import create_app, db
from app.models import User

app = create_app()
# this file is added to populate some test data into the database. 

with app.app_context():
    
    #User.query.delete()

    # -------------------------
    # Create sample users
    # -------------------------

    user1 = User(
        full_name="Liam Thompson",
        email="liam.thompson@example.com",
        password_hash="hashed_pw",
        title="Project Lead",
        location="Perth, Australia",
        timezone="Australia/Perth"
        avatar_url="https://example.com/avatars/liam.png",
    )

    user2 = User(
        full_name="Olivia Walker",
        email="olivia.walker@example.com",
        password_hash="hashed_pw",
        title="UI/UX Designer",
        location="Sydney, Australia",
        timezone="Australia/Sydney",
        avatar_url="https://example.com/avatars/olivia.png",
    )

    user3 = User(
        full_name="Noah Williams",
        email="noah.williams@example.com",
        password_hash="hashed_pw",
        title="Backend Developer",
        location="Melbourne, Australia",
        timezone="Australia/Melbourne",
        avatar_url="https://example.com/avatars/noah.png",
    )

    # Add users to session
    db.session.add_all([user1, user2, user3])

    # Commit to database
    db.session.commit()

    print("Users seeded successfully.")