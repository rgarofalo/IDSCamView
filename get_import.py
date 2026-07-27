import ast
import os
import glob

py_files = []
py_directory = "src"


def find_imports_in_file(file_path, only_from=True):
    global py_files, py_directory
    with open(file_path, "r", encoding="utf-8") as file:
        node = ast.parse(file.read(), filename=file_path)

    imports = set()

    for n in ast.walk(node):
        if isinstance(n, ast.Import) and not only_from:
            for alias in n.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module is not None:
                imp = n.module.split(".")[0]
                if py_directory + "\\" + imp + ".py" in py_files:
                    continue
                imports.add(imp)
                for alias in n.names:
                    import_name = alias.name
                    imports.add(imp+"."+import_name)
                

                # imports.add(imp)

    return imports


def find_imports_in_directory(directory, only_from=True):
    global py_files, py_directory

    py_directory = directory

    all_imports = set()
    py_files = glob.glob(os.path.join(directory, "*.py"))

    for py_file in py_files:
        all_imports.update(find_imports_in_file(py_file, only_from))

    return all_imports


def main():
    directory = "src"  # Replace with your directory containing .py files
    imports = find_imports_in_directory(directory, False)

    print("Libraries used:")
    for imp in sorted(imports):
        print(imp)


if __name__ == "__main__":
    main()
