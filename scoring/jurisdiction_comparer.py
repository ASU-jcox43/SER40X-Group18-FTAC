"""
Jurisdiction comparison file.

This module takes the JSON file with all the computed scores, and allows the user
to pick two to compare.

"""

import json
from pathlib import Path
import re


def load_file(file_path):
    """
        Function for loading JSON.

        Loads the JSON file and returns the results of it.

        Args:
            file_path: The path of the JSON file to use.
    """
    with open(file_path, "r") as f:
        return json.load(f)


def search_file(term, data):
    """
        Function for searching phrases.

        Searches the file for a term given the data.

        Args:
            term: The term to search for.
            data: The data from the JSON file.
    """
    regex = re.compile(term, re.IGNORECASE)

    result = []
    for name in data.keys():
        if bool(re.search(term, name, re.IGNORECASE)):
            result.append(name)

    return result


def compare_choices(prompt, data):
    """
        Prompts the user for a file name.

        Finds the matches and returns the number of matches for a given term.

        Args:
            prompt: What to ask the user for.
            data: The data from the JSON file.
    """

    while True:
        first_file = input(prompt).strip()
        if not first_file:
            print("Please enter the name of the first file.")
            continue

        matches = search_file(first_file, data)

        if not matches:
            print("There were not matches for that file, please try again.")
            continue
        elif len(matches) > 1:
            print("Multiple matches to this file were found:")
            for i, m in enumerate(matches, 1):
                print(f" {i}. {m}")
            choice = input("Type the number for the file you meant:")
            if choice.isdigit() and 1 <= int(choice) <= len(matches):
                return matches[int(choice) - 1]
            else:
                print("Invalid number, please try again.")
        else:
            return matches[0]


def main():
    file_path = Path("friendliness_summary.json")
    if not file_path.exists():
        print(f"File could not be found at {file_path}")
        return

    data = load_file(file_path)

    for names in data.keys():
        print(names)

    print("Pick two jurisdiction files to compare:")
    first_file = compare_choices("First name: ", data)
    second_file = compare_choices("Second name: ", data)

    first_score = data[first_file]
    second_score = data[second_file]

    if first_score > second_score:
        print(
            f"{first_file} has a higher score of {first_score} compared to {second_file} with a score of {second_score}.")
    elif second_score > first_score:
        print(
            f"{second_file} has a higher score of {second_score} compared to {first_file} with a score of {first_score}.")
    else:
        print(f"Both files have the same score of {first_score}.")


if __name__ == "__main__":
    main()
