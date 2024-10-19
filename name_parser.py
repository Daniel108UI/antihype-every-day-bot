import os


def parse_filenames(directory):
    try:
        # Получаем список файлов в указанной директории
        files = os.listdir(directory)

        # Фильтруем только файлы, исключая директории
        files = [f for f in files if os.path.isfile(os.path.join(directory, f))]

        # Выводим имена файлов в одинарных кавычках
        for file in files:
            print(f"'{file}',")

    except FileNotFoundError:
        print(f"Директория {directory} не найдена.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


# Пример использования
directory_path = r'C:\Users\Daniel\Downloads\n'
parse_filenames(directory_path)
