from faker import Faker
import random

fake = Faker("ru_RU")

def fake_passport():
    return {
        "series": f"{random.randint(1000,9999)}",
        "number": f"{random.randint(100000,999999)}",
        "issued": fake.company()
    }

def fake_student():
    passport = fake_passport()
    return {
        "last_name": fake.last_name(),
        "first_name": fake.first_name(),
        "middle_name": fake.middle_name(),
        "passport_series": passport["series"],
        "passport_number": passport["number"],
        "passport_issued": passport["issued"],
        "citizenship": "Россия",
        "registration_addr": fake.address(),
        "birth_date": fake.date_of_birth(minimum_age=17, maximum_age=30)
    }
