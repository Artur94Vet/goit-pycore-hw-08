from collections import UserDict
from colorama import init, Fore, Style
import re
import os
#----------------------------------------------------
'''
я хз ..вже очі вилазять.. дз по ооп в порівнянні з теорією не важке, але змінювати вже існуюче серед ночі не дуже легко)
використовую чат GPT для перевірок та підсказок// я не знаю, як тримати це все в голові, окрім того як кожен день кодити ( щей бажано на роботі якісь кейси пробуваи виконати)

'''
init(autoreset=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(BASE_DIR, "phone_list.txt")

def input_error(func):

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return Fore.RED + "Record with such name not found." + Style.RESET_ALL
        except ValueError as ve:
            return Fore.RED + str(ve) + Style.RESET_ALL
        except IndexError:
            return Fore.RED + "Enter the argument for the command." + Style.RESET_ALL
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
#-----------------------------------------------------------------------------------------------
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
            raise ValueError("The name cannot be empty.")
        super().__init__(value.strip())

class Phone(Field):
    """
    Клас для зберігання номера телефону.
    Номер телефону повинен відповідати українському формату: +380XXXXXXXXX.
    """
    def __init__(self, value: str):
        pattern = r"^\+380\d{9}$"
        if not re.fullmatch(pattern, value):
            raise ValueError("The phone number must be in the format +380XXXXXXXXX (10 digits after +380).")
        super().__init__(value)

class Record:
    """
    Клас для зберігання інформації про контакт.
    Містить об'єкт Name та список об'єктів Phone.
    """
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: list[Phone] = []

    def add_phone(self, phone: str) -> None:
        """Додає новий номер телефону до запису."""
        phone_obj = Phone(phone)
        # Якщо номер вже є, можна попередити користувача (або просто додати)
        if any(p.value == phone_obj.value for p in self.phones):
            raise ValueError("Such number already exists for the contact.")
        self.phones.append(phone_obj)

    def remove_phone(self, phone: str) -> None:
        """Видаляє номер телефону зі запису.
        Піднімає ValueError, якщо телефон не знайдено.
        """
        for p in self.phones:
            if p.value == phone:
                self.phones.remove(p)
                return
        raise ValueError(f"Phone  {phone} not found in the record.")

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """Редагує існуючий номер телефону на новий.
        Піднімає ValueError, якщо старий номер не знайдено.
        """
        for index, p in enumerate(self.phones):
            if p.value == old_phone:
                self.phones[index] = Phone(new_phone)
                return
        raise ValueError(f"Phone {old_phone} not found for editing.")

    def find_phone(self, phone: str) -> str:
        """Повертає номер телефону, якщо він знайдений.
        Піднімає ValueError, якщо телефон не знайдено.
        """
        for p in self.phones:
            if p.value == phone:
                return p.value
        raise ValueError(f"Phone {phone} not found.")

    def __str__(self) -> str:
        phones_str = "; ".join(p.value for p in self.phones) if self.phones else "No phones."
        return f"Contact name: {self.name.value}, phones: {phones_str}"

class AddressBook(UserDict):
    """
    Клас для управління записами контактів.
    Реалізує завантаження та збереження даних з/у файл, а також операції додавання,
    пошуку та видалення записів.
    """
    def __init__(self, file_name: str):
        super().__init__()
        self.file_name = file_name
        self.load_contacts()

    def load_contacts(self):
        """
        Завантажує контакти з файлу.
        Підтримує рядки з форматом "name:phone" або "name,phone".
        Якщо файл відсутній, адресна книга залишається порожньою.
        """
        if os.path.exists(self.file_name):
            with open(self.file_name, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    if ":" in line:
                        name_str, phone_str = line.split(":", 1)
                    elif "," in line:
                        name_str, phone_str = line.split(",", 1)
                    else:
                        continue
                    # Якщо контакт вже існує, додаємо номер до нього
                    try:
                        if name_str in self.data:
                            self.data[name_str].add_phone(phone_str.strip())
                        else:
                            record = Record(name_str)
                            record.add_phone(phone_str.strip())
                            self.data[name_str] = record
                    except ValueError as e:
                        print(Fore.RED + f"Skipping incorrect record: {e}" + Style.RESET_ALL)

    def save_contacts(self):
        """
        Зберігає контакти до файлу.
        Записує кожен номер у форматі "name:phone".
        Якщо контакт містить декілька номерів, кожен номер записується окремим рядком.
        """
        with open(self.file_name, "w", encoding="utf-8") as file:
            for record in self.data.values():
                for phone in record.phones:
                    file.write(f"{record.name.value}:{phone.value}\n")

    @input_error
    def add_record(self, args):
        """
        Додає запис або номер телефону до існуючого запису.
        Команда очікує щонайменше 2 аргументи: name та phone.
        Якщо запис з даним ім'ям вже існує, додається новий номер телефону.
        """
        if len(args) < 2:
            raise IndexError
        name, phone = args[0], args[1]
        if name in self.data:
            # Якщо запис існує, намагаємося додати номер телефону
            self.data[name].add_phone(phone)
        else:
            record = Record(name)
            record.add_phone(phone)
            self.data[name] = record
        self.save_contacts()
        return Fore.GREEN + "Contact added." + Style.RESET_ALL

    @input_error
    def change_record(self, args):
        """
        Редагує існуючий номер телефону контакту.
        Команда очікує 3 аргументи: name, old_phone та new_phone.
        """
        if len(args) < 3:
            raise IndexError
        name, old_phone, new_phone = args[0], args[1], args[2]
        if name in self.data:
            self.data[name].edit_phone(old_phone, new_phone)
            self.save_contacts()
            return Fore.GREEN + "Contact updated." + Style.RESET_ALL
        else:
            raise KeyError

    @input_error
    def show_record(self, args):
        """
        Повертає інформацію про контакт (всі номери телефону) за іменем.
        Команда очікує 1 аргумент: name.
        """
        if len(args) < 1:
            raise IndexError
        name = args[0]
        if name in self.data:
            return Fore.GREEN + str(self.data[name]) + Style.RESET_ALL
        else:
            raise KeyError

    def show_all(self):
        """
        Повертає рядок з усіма контактами та їх номерами.
        Якщо записів немає, повертається відповідне повідомлення.
        """
        if not self.data:
            return Fore.RED + "No contacts found." + Style.RESET_ALL
        result = []
        for record in self.data.values():
            result.append(str(record))
        return "\n".join(result)

    @input_error
    def delete_record(self, args):
        """
        Видаляє запис контакту за іменем.
        Команда очікує 1 аргумент: name.
        """
        if len(args) < 1:
            raise IndexError
        name = args[0]
        if name in self.data:
            del self.data[name]
            self.save_contacts()
            return Fore.GREEN + "Contact deleted." + Style.RESET_ALL
        else:
            raise KeyError
#-------------------------------------------------------------------------------
def main():
    address_book = AddressBook(FILE_NAME)
    print(Fore.CYAN + "Welcome to the assistant bot!" + Style.RESET_ALL)
    while True:
        user_input = input(Fore.CYAN + "Enter a command: " + Style.RESET_ALL)
        command, args = parse_input(user_input)
        if command in ("exit", "close"):
            print(Fore.MAGENTA + "Good bye!" + Style.RESET_ALL)
            break
        elif command == "hello":
            print(Fore.CYAN + "How can I help you?" + Style.RESET_ALL)
        elif command == "add":
            print(address_book.add_record(args))
        elif command == "change":
            print(address_book.change_record(args))
        elif command == "phone":
            print(address_book.show_record(args))
        elif command == "all":
            print(address_book.show_all())
        elif command == "delete":
            print(address_book.delete_record(args))
        else:
            print(Fore.RED + "Invalid command. Please try again." + Style.RESET_ALL)

if __name__ == "__main__":
    main()
