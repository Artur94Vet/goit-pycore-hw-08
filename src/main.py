from collections import UserDict
from colorama import init, Fore, Style
import re
import os
from datetime import datetime, date, timedelta

# Ініціалізація colorama
init(autoreset=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(BASE_DIR, "phone_list.txt")

def input_error(func):
    # Декоратор для обробки помилок вводу та виводу повідомлень англійською
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
    # Функція для розбору введеного рядка користувача
    parts = user_input.split()
    if not parts:
        return "", []
    command = parts[0].strip().lower()
    args = parts[1:]
    return command, args

#================== Базові класи ============================
class Field:
    """Базовий клас для полів запису."""
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    """Клас для зберігання імені контакту. Ім'я є обов'язковим полем."""
    def __init__(self, value: str):
        if not value.strip():
            raise ValueError("Name cannot be empty.")
        super().__init__(value.strip())

class Phone(Field):
    """
    Клас для зберігання номера телефону.
    Номер телефону має відповідати формату +380XXXXXXXXX (10 цифр після +380).
    """
    def __init__(self, value: str):
        pattern = r"^\+380\d{9}$"
        if not re.fullmatch(pattern, value):
            raise ValueError("Phone number must be in the format +380XXXXXXXXX (10 digits after +380).")
        super().__init__(value)

class Birthday(Field):
    """
    Клас для зберігання дня народження.
    Очікуваний формат: DD.MM.YYYY.
    """
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
    """
    Клас для зберігання інформації про контакт.
    Містить об'єкт Name, список об'єктів Phone та опціонально Birthday.
    """
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
        # Видаляє номер телефону зі запису.
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError(f"Phone {phone} not found in the record.")

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        # Редагує існуючий номер телефону.
        for index, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[index] = Phone(new_phone)
                return
        raise ValueError(f"Phone {old_phone} not found for editing.")

    def add_birthday(self, birthday_str: str) -> None:
        # Додає або оновлює дату народження контакту.
        self.birthday = Birthday(birthday_str)

    def days_to_birthday(self) -> int:
        # Обчислює кількість днів до наступного дня народження.
        # Повертає -1, якщо дата народження не встановлена.
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
    """
    Клас для управління контактами.
    Реалізує завантаження та збереження даних з/у файл, а також операції додавання,
    пошуку та видалення записів.
    Формат збереження:
      - Для номера телефону: name:phone:{phone}
      - Для дня народження: name:birthday:{date in DD.MM.YYYY format}
    """
    def __init__(self, file_name: str):
        super().__init__()
        self.file_name = file_name
        self.load_contacts()

    def load_contacts(self):
        # Завантажує контакти з файлу.
        if os.path.exists(self.file_name):
            with open(self.file_name, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(":")
                    # Підтримка старого формату "name:phone"
                    if len(parts) == 2:
                        name_str, value = parts[0], parts[1]
                        field_type = "phone"
                    elif len(parts) == 3:
                        name_str, field_type, value = parts[0], parts[1], parts[2]
                    else:
                        continue
                    try:
                        if name_str in self.data:
                            record = self.data[name_str]
                        else:
                            record = Record(name_str)
                            self.data[name_str] = record
                        if field_type == "phone":
                            record.add_phone(value.strip())
                        elif field_type == "birthday":
                            record.add_birthday(value.strip())
                    except ValueError as e:
                        print(Fore.RED + f"Skipped invalid record: {e}" + Style.RESET_ALL)

    def save_contacts(self):
        # Зберігає контакти у файл.
        with open(self.file_name, "w", encoding="utf-8") as file:
            for record in self.data.values():
                if record.birthday is not None:
                    file.write(f"{record.name.value}:birthday:{record.birthday}\n")
                for phone in record.phones:
                    file.write(f"{record.name.value}:phone:{phone.value}\n")

    def get_upcoming_birthdays(self, days: int = 7):
        # Повертає список контактів з днями народження, що настануть у найближчі 'days' днів.
        # Повертається список кортежів: (ім'я, дата народження, кількість днів до дня народження)
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
        # Повертає рядок з усіма контактами або повідомлення, якщо контактів немає.
        if not self.data:
            return Fore.RED + "No contacts found." + Style.RESET_ALL
        result = []
        for record in self.data.values():
            result.append(str(record))
        return "\n".join(result)

#================== Функції-команди ============================
@input_error
def add_contact(args, book: AddressBook):
    # Додає або оновлює контакт з номером телефону.
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
    book.save_contacts()
    return message

@input_error
def change_contact(args, book: AddressBook):
    # Редагує існуючий номер телефону контакту.
    if len(args) < 3:
        raise IndexError
    name, old_phone, new_phone = args[0], args[1], args[2]
    if name not in book.data:
        raise KeyError
    record = book.data[name]
    record.edit_phone(old_phone, new_phone)
    book.save_contacts()
    return "Contact updated."

@input_error
def show_phone(args, book: AddressBook):
    # Показує інформацію про контакт.
    if len(args) < 1:
        raise IndexError
    name = args[0]
    if name not in book.data:
        raise KeyError
    return Fore.GREEN + str(book.data[name]) + Style.RESET_ALL

@input_error
def add_birthday(args, book: AddressBook):
    # Додає або оновлює дату народження контакту.
    if len(args) < 2:
        raise IndexError
    name, birthday_str = args[0], args[1]
    if name not in book.data:
        raise KeyError("Contact not found.")
    record = book.data[name]
    record.add_birthday(birthday_str)
    book.save_contacts()
    return "Birthday added."

@input_error
def show_birthday(args, book: AddressBook):
    # Показує дату народження контакту.
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
    # Повертає список контактів з майбутніми днями народження.
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No contacts with upcoming birthdays."
    lines = []
    for name, bday_str, days_left in upcoming:
        lines.append(f"{name} - {bday_str} (in {days_left} days)")
    return "\n".join(lines)

@input_error
def delete_contact(args, book: AddressBook):
    # Видаляє контакт з адресної книги.
    if len(args) < 1:
        raise IndexError
    name = args[0]
    if name in book.data:
        del book.data[name]
        book.save_contacts()
        return "Contact deleted."
    else:
        raise KeyError

#================== Головна функція ============================
def main():
    book = AddressBook(FILE_NAME)
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

if __name__ == "__main__":
    main()
