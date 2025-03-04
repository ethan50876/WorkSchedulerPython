import csv
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict

@dataclass
class Employee:
    """
A class to represent an Employee.

Attributes:
    name (str): The name of the employee.
    availability (Tuple[int, int]): Start and end hours of availability, (start_hour, end_hour)
    min_hours (int): The minimum number of hours the employee can work.
    max_hours (int): The maximum number of hours the employee can work.
    roles (Set[str]): A set of roles the employee can perform, eg. set[On-Floor, Cashier]
    days_off (Set[str]): A set of days the employee is not available to work, eg
"""
    name: str
    availability: Tuple[int, int] 
    min_hours: int
    max_hours: int
    roles: Set[str]
    days_off: Set[str]

ShiftSchedule = Dict[str, Dict[int, Dict[str, List[Employee]]]]  # {Day: {Hour: {Role: [Employee]}}}

@dataclass
class EmployerRequirements:
    """
EmployerRequirements is a data class that holds the requirements for an employer's scheduling needs.

Attributes:
    work_hours (Tuple[int, int]): A Tuple holding the opening and closing hours of the workplace.
    shift_lengths (Tuple[int, int]): A tuple representing the minimum and maximum lengths of shifts.
    critical_minimums (Dict[str, int]): A dictionary mapping roles to the minimum number of employees required for each role.
"""
    work_hours: Tuple[int, int]  # (open_hour, close_hour)
    shift_lengths: Tuple[int, int]  # (min_shift, max_shift)
    critical_minimums: Dict[str, int]  # {Role: Minimum Employees Required}   

def parse_employee_data(file_path: str) -> List[Employee]:
    """
    Parses employee data from a CSV file and returns a list of Employee objects.
    Args:
        file_path (str): The path to the CSV file containing employee data.
    Returns:
        List[Employee]: A list of Employee objects parsed from the CSV file.
        If the file is not found or an error occurs during parsing, an empty list is returned.
    The CSV file is expected to have the following columns:
        - Name: The name of the employee.
        - Hours Available: The hours the employee is available, in the format 'start-end'.
        - Min Hours: The minimum number of hours the employee can work.
        - Max Hours: The maximum number of hours the employee can work.
        - Roles: The roles the employee can perform, separated by commas.
        - Days Off: The days the employee has off, separated by commas (optional).
    Raises:
        FileNotFoundError: If the specified file is not found.
        Exception: If an error occurs during parsing.
    """
    employees = []
    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                employees.append(Employee(
                    name=row["Name"].strip(),
                    availability=tuple(map(int, row["Hours Available"].split('-'))),
                    min_hours=int(row["Min Hours"]),
                    max_hours=int(row["Max Hours"]),
                    roles=set(map(str.strip, row["Roles"].replace('"', '').split(','))),  # Fix: Remove quotes
                    days_off=set(map(str.strip, row["Days Off"].replace('"', '').split(','))) if row["Days Off"].strip() else set()
                ))
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error parsing employee file: {e}")
        return []

    return employees


def parse_employer_requirements(file_path: str) -> EmployerRequirements:
    """
    Parses the employer requirements from a CSV file.
    The CSV file must have the following columns:
    - Roles: The role name.
    - Critical Minimums: The minimum number of employees required for the role.
    - Scheduling Hours: The range of hours during which scheduling is allowed, in the format 'start-end'.
    - ShiftLengths: The range of shift lengths allowed, in the format 'min-max'.
    Args:
        file_path (str): The path to the CSV file containing employer requirements.
    Returns:
        EmployerRequirements: An object containing the parsed employer requirements, including work hours,
                              shift lengths, and critical minimums for each role. Returns None if the file
                              is not found or if there is an error during parsing.
    """
    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            critical_minimums = {}
            work_hours = (0, 0)
            shift_lengths = (0, 0)

            for row in reader:
                role = row["Roles"].strip()
                min_count = int(row["Critical Minimums"].strip())
                critical_minimums[role] = min_count

                work_hours = tuple(map(int, row["Scheduling Hours"].split('-')))
                shift_lengths = tuple(map(int, row["ShiftLengths"].split('-')))

            return EmployerRequirements(
                work_hours=work_hours,
                shift_lengths=shift_lengths,
                critical_minimums=critical_minimums
            )

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error parsing employer requirements file: {e}")
        return None


# test driver
if __name__ == "__main__":
    EMPLOYEE_FILE = "data/employees.csv"
    REQUIREMENTS_FILE = "data/requirements.csv"

    employees = parse_employee_data(EMPLOYEE_FILE)
    employer_requirements = parse_employer_requirements(REQUIREMENTS_FILE)

    print("Parsed Employees:")
    for emp in employees:
        print(emp)

    print("\nParsed Employer Requirements:")
    print(employer_requirements)
