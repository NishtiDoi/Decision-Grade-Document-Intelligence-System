def parse_age(value):
    try:
        age = int(value)
        if age < 0:
            raise ValueError("Age cannot be negative")
        return age

    except ValueError as e:
        print(f"Invalid input: {e}")
        raise
