import datetime
import random


def random_date() -> datetime.datetime:
    year = random.randint(2000, 2025)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    date_str = f"{year:04d}-{month:02d}-{day:02d}T00:00:00Z"
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
