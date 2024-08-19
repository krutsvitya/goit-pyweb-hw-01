from collections import UserDict
from datetime import datetime, date, timedelta
import pickle
from abc import ABC, abstractmethod


class View(ABC):
    @abstractmethod
    def show_contacts(self, contacts):
        pass

    @abstractmethod
    def show_message(self, message):
        pass

    @abstractmethod
    def show_commands(self, commands):
        pass


class ConsoleView(View):
    def show_contacts(self, contacts):
        print("Contacts list:")
        for record in contacts.values():
            print(record)

    def show_message(self, message):
        print(message)

    def show_commands(self, commands):
        print("Available commands:")
        for command in commands:
            print(command)


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if len(value) == 10 and value.isdigit():
            super().__init__(value)
        else:
            raise ValueError("Phone number must contain 10 digits.")


class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def __str__(self):
        phones = ', '.join(p.value for p in self.phones)
        birthday = self.birthday.value if self.birthday else "No birthday"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def add_birthday(self, date):
        self.birthday = Birthday(date)

    def remove_phone(self, phone):
        phone_instance = self.find_phone(phone)
        if phone_instance:
            self.phones.remove(phone_instance)
        else:
            raise ValueError("Phone number not found")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def edit_phone(self, old_phone, new_phone):
        phone_instance = self.find_phone(old_phone)
        if phone_instance:
            index = self.phones.index(phone_instance)
            self.phones[index] = Phone(new_phone)
        else:
            raise ValueError("Old phone number not found")


class AddressBook(UserDict):
    def __str__(self):
        result = []
        for record in self.data.values():
            result.append(str(record))
        return "\n".join(result)

    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday:
                birthday_this_year = datetime.strptime(record.birthday.value, "%d.%m.%Y").date().replace(
                    year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                if 0 <= (birthday_this_year - today).days <= days:
                    birthday_this_year = adjust_for_weekend(birthday_this_year)
                    congratulation_date_str = date_to_string(birthday_this_year)
                    upcoming_birthdays.append({"name": record.name.value, "birthday": congratulation_date_str})
        return upcoming_birthdays


def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:
        return find_next_weekday(birthday, 0)
    return birthday


def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def date_to_string(date):
    return date.strftime("%d.%m.%Y")


# Bot
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found"
        except IndexError:
            return "Insufficient arguments provided"

    return inner


def parse_input(user_input):
    cmd, *args = user_input.split()
    return cmd.strip().lower(), args


@input_error
def add_contact(args, book):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    record.add_phone(phone)
    return message


@input_error
def change_phone(args, contacts):
    name, phone = args
    contacts[name] = phone
    return 'Phone number was updated'


@input_error
def give_phone(args, contacts):
    name = args[0]
    return contacts[name]


@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)
    if record is None:
        return "Contact not found."
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday is on {record.birthday.value}"
    return "Birthday not found for this contact."


@input_error
def birthdays(book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    return "\n".join(
        [f"{entry['name']}: {entry['birthday']}" for entry in upcoming_birthdays]) or "No upcoming birthdays."


def save_data(book, filename="addressbook.pkl"):
    with open(filename, 'wb') as file:
        pickle.dump(book, file)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return AddressBook()


def main(view):
    book = load_data()
    view.show_message("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            view.show_message("Good bye!")
            break
        elif command == "hello":
            view.show_message("How can I help you?")
        elif command == "add":
            view.show_message(add_contact(args, book))
        elif command == "change":
            view.show_message(change_phone(args, book))
        elif command == "phone":
            view.show_message(give_phone(args, book))
        elif command == "all":
            view.show_contacts(book)
        elif command == "add-birthday":
            view.show_message(add_birthday(args, book))
        elif command == "show-birthday":
            view.show_message(show_birthday(args, book))
        elif command == "birthdays":
            view.show_message(birthdays(book))
        elif command == "help":
            view.show_commands(["hello", "add", "change", "phone", "all", "add-birthday", "show-birthday", "birthdays", "help", "close", "exit"])
        else:
            view.show_message("Invalid command.")

    save_data(book)


if __name__ == "__main__":
    console_view = ConsoleView()
    main(console_view)
