from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import Question

QUESTIONS = [
    ("technical", "easy", "Reverse a linked list in place. Walk through your approach before writing code."),
    ("technical", "medium", "Design a rate limiter for an API. What data structure would you use and why?"),
    ("technical", "medium", "Given a list of user events with timestamps, find the busiest one-hour window. Discuss time and space complexity."),
    ("technical", "hard", "Implement an LRU cache with O(1) get and put. Explain which data structures you need and why each one is required."),
    ("technical", "easy", "What is the difference between an index on one column and a composite index on two? When would a composite index not help?"),
    ("behavioral", "easy", "Tell me about a time you disagreed with a teammate. How did you resolve it?"),
    ("behavioral", "medium", "Describe a project that did not go the way you planned. What did you do, and what would you do differently?"),
    ("behavioral", "medium", "Tell me about a time you received critical feedback on your work. How did you react to it?"),
    ("behavioral", "hard", "Describe a situation where you had to make a technical decision without enough information. How did you decide, and how did it turn out?"),
    ("system_design", "medium", "Design a URL shortener that handles 100M redirects per day."),
    ("system_design", "medium", "Design the backend for a notification system that sends email, SMS, and push. How do you handle a provider going down?"),
    ("system_design", "hard", "Design a system that grades AI interview answers. Grading takes 5-15 seconds per answer. How do you keep the API responsive?"),
]


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.execute(select(func.count()).select_from(Question)).scalar_one()
        if existing:
            print(f"{existing} questions already present, skipping seed")
            return

        db.add_all([Question(type=t, difficulty=d, prompt=p) for t, d, p in QUESTIONS])
        db.commit()
        print(f"Inserted {len(QUESTIONS)} questions")
    finally:
        db.close()


if __name__ == "__main__":
    seed()