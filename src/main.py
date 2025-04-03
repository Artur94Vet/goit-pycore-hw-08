from collections import UserDict
from colorama import init, Fore, Style
import re
import pickle
import os
from datetime import datetime, date, timedelta
'''
старі коментарі видалено, нові коментарі додано
відповідно до домашнього завдання
додано функцію для збереження адресної книги у файл за допомогою pickle
новий код прокоментовано

цього разу вже по лінивому скопіював папку з проєктом і перепідв'язав до нового віддаленого git репозиторію

а ще сьогодні скачав github copliot і він прямо зараз допомагає мені писати цей коментар (хоча я ним ще ніколи не користувався)
якщо чесно, то я вражений, бо він з кількох слів зрозумів, що я хочу написати в коментарі (це ще я його в коді не пробував)

капець якийсь, вражає..

доречі, тепер я зрозумів чому ви писали в минулих коментарях до дз, що я трішки забігав наперед, з цим збереженням якось набагато краще)
я просто думав, що перші дз, ми мали автоматични застосовувати на практиці в створенні консольного чат бота (в мене дійсно на початку було багато лишнього)


'''
init(autoreset=True)

# Функції для серіалізації/десеріалізації за допомогою pickle

def save_data(book, filename="addressbook.pkl"):
    # Зберігає стан адресної книги у файл за допомогою pickle
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    # Завантажує стан адресної книги з файлу; повертає нову, якщо файл не знайдено
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return Fore.RED + "Record with such name not found." + Style.RESET_ALL
        except ValueError as ve:
            return Fore.RED + str(ve) + Style.RESET_ALL
        except IndexError:
            return Fore.RED + "Please enter the required arguments for the command." + Style.RESET_ALL
        except Exception as e:
            return Fore.RED + f"Unexpected error: {e}" + Style.RESET_ALL
    return inner

def parse_input(user_input):
    parts = user_input.split()
    if not parts:
        return "", []
    command = parts[0].strip().lower()
    args = parts[1:]
    return command, args

#================== Базові класи ============================
class Field:
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value: str):
        if not value.strip():
            raise ValueError("Name cannot be empty.")
        super().__init__(value.strip())

class Phone(Field):
    def __init__(self, value: str):
        pattern = r"^\+380\d{9}$"
        if not re.fullmatch(pattern, value):
            raise ValueError("Phone number must be in the format +380XXXXXXXXX (10 digits after +380).")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value: str):
        try:
            birthday_date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY.")
        super().__init__(birthday_date)

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")

#================== Клас Record ============================
class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    def add_phone(self, phone: str) -> None:
        # Додає новий номер телефону до запису.
        phone_obj = Phone(phone)
        if any(p.value == phone_obj.value for p in self.phones):
            raise ValueError("Such number already exists for the contact.")
        self.phones.append(phone_obj)

    def remove_phone(self, phone: str) -> None:
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError(f"Phone {phone} not found in the record.")

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        for index, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[index] = Phone(new_phone)
                return
        raise ValueError(f"Phone {old_phone} not found for editing.")

    def add_birthday(self, birthday_str: str) -> None:
        self.birthday = Birthday(birthday_str)

    def days_to_birthday(self) -> int:
        if self.birthday is None:
            return -1
        bday: date = self.birthday.value
        today = date.today()
        next_birthday = bday.replace(year=today.year)
        if next_birthday < today:
            next_birthday = bday.replace(year=today.year + 1)
        return (next_birthday - today).days

    def __str__(self) -> str:
        phones_str = ", ".join(p.value for p in self.phones) if self.phones else "No phones"
        birthday_str = f", Birthday: {self.birthday}" if self.birthday else ""
        return f"Name: {self.name.value}, Phones: {phones_str}{birthday_str}"

#================== Клас AddressBook ============================
class AddressBook(UserDict):
    def __init__(self):
        super().__init__()

    def get_upcoming_birthdays(self, days: int = 7):
        result = []
        today = date.today()
        for record in self.data.values():
            if record.birthday is not None:
                bday: date = record.birthday.value
                next_bday = bday.replace(year=today.year)
                if next_bday < today:
                    next_bday = bday.replace(year=today.year + 1)
                days_left = (next_bday - today).days
                if 0 <= days_left <= days:
                    result.append((record.name.value, next_bday.strftime("%d.%m.%Y"), days_left))
        return result

    def show_all(self):
        if not self.data:
            return Fore.RED + "No contacts found." + Style.RESET_ALL
        result = []
        for record in self.data.values():
            result.append(str(record))
        return "\n".join(result)

#================== Функції-команди ============================
@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError
    name, phone, *_ = args
    record = book.data.get(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.data[name] = record
        message = "Contact added."
    record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise IndexError
    name, old_phone, new_phone = args[0], args[1], args[2]
    if name not in book.data:
        raise KeyError
    record = book.data[name]
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."

@input_error
def show_phone(args, book: AddressBook):
    if len(args) < 1:
        raise IndexError
    name = args[0]
    if name not in book.data:
        raise KeyError
    return Fore.GREEN + str(book.data[name]) + Style.RESET_ALL

@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise IndexError
    name, birthday_str = args[0], args[1]
    if name not in book.data:
        raise KeyError("Contact not found.")
    record = book.data[name]
    record.add_birthday(birthday_str)
    return "Birthday added."

@input_error
def show_birthday(args, book: AddressBook):
    if len(args) < 1:
        raise IndexError
    name = args[0]
    if name not in book.data:
        raise KeyError("Contact not found.")
    record = book.data[name]
    if record.birthday is None:
        return "Birthday not set."
    return f"Birthday for {name}: {record.birthday}"

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No contacts with upcoming birthdays."
    lines = []
    for name, bday_str, days_left in upcoming:
        lines.append(f"{name} - {bday_str} (in {days_left} days)")
    return "\n".join(lines)

@input_error
def delete_contact(args, book: AddressBook):
    if len(args) < 1:
        raise IndexError
    name = args[0]
    if name in book.data:
        del book.data[name]
        return "Contact deleted."
    else:
        raise KeyError

#================== Головна функція ============================
def main():
    # Завантаження адресної книги з файлу або створення нової, якщо файл відсутній
    book = load_data()
    print(Fore.CYAN + "Welcome to the assistant bot!" + Style.RESET_ALL)
    while True:
        user_input = input(Fore.CYAN + "Enter command: " + Style.RESET_ALL)
        command, args = parse_input(user_input)
        if command in ["close", "exit"]:
            print(Fore.MAGENTA + "Goodbye!" + Style.RESET_ALL)
            break
        elif command == "hello":
            print(Fore.CYAN + "How can I help you?" + Style.RESET_ALL)
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(book.show_all())
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        elif command == "delete":
            print(delete_contact(args, book))
        else:
            print(Fore.RED + "Unknown command. Please try again." + Style.RESET_ALL)
    # Збереження адресної книги при виході з програми
    save_data(book)

if __name__ == "__main__":
    main()