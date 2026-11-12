from datetime import datetime, timedelta, timezone
from app.database import session
from app.models.ride import User, Ride

def seed_database():
    db = session()
    try:
        dummy_user = User(
            first_name="Shreesha",
            last_name="Rao",
            email="shreesha@goa.bits-pilani.ac.in",
            contact="9876543210"
        )
        db.add(dummy_user)
        db.commit()
        db.refresh(dummy_user)
        print(f"Created User with UUID: {dummy_user.id}")

        ride_1 = Ride(
            ride_owner=dummy_user.id,
            origin="Dabolim Airport",
            destination="BITS Pilani Goa Campus",
            expected_arrival_time=datetime.now(timezone.utc) + timedelta(days=1),
            total_accommodation=3,
            expected_luggage=2
        )
        
        ride_2 = Ride(
            ride_owner=dummy_user.id,
            origin="Madgaon Railway Station",
            destination="BITS Pilani Goa Campus",
            expected_arrival_time=datetime.now(timezone.utc) + timedelta(days=2),
            total_accommodation=4,
            expected_luggage=1
        )

        db.add_all([ride_1, ride_2])
        db.commit()
        print("Successfully seeded database with mock rides!")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()