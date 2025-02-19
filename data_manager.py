import csv
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict

@dataclass
class Employee:
    name: str
    availability: Tuple[int, int]  # (start_hour, end_hour)
    min_hours: int
    max_hours: int
    roles: Set[str]
    days_off: Set[str]

@dataclass
class EmployerRequirements:
    work_hours: Tuple[int, int]  # (open_hour, close_hour)
    shift_lengths: Tuple[int, int]  # (min_shift, max_shift)
    critical_minimums: Dict[str, int]  # {Role: Minimum Employees Required}

def parse_employee_data(file_path: str) -> List[Employee]:
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
                    roles=set(map(str.strip, row["Roles"].split(','))),
                    days_off=set(map(str.strip, row["Days Off"].split(','))) if row["Days Off"] else set()
                ))
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error parsing employee file: {e}")
        return []

    return employees

def parse_employer_requirements(file_path: str) -> EmployerRequirements:
    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            req_data = {}
            for row in reader:
                req_data = {
                    "work_hours": tuple(map(int, row["Scheduling Hours"].split('-'))),
                    "shift_lengths": tuple(map(int, row["ShiftLengths"].split('-'))),
                    "critical_minimums": {role.strip(): int(min_count) for role, min_count in zip(row["Roles"].split(','), row["Critical Minimums"].split(','))}
                }
                break  
            return EmployerRequirements(**req_data)

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error parsing employer requirements file: {e}")
        return None

# test driver (data still missing)
if __name__ == "__main__":
    EMPLOYEE_FILE = "employees.csv"
    REQUIREMENTS_FILE = "requirements.csv"

    employees = parse_employee_data(EMPLOYEE_FILE)
    employer_requirements = parse_employer_requirements(REQUIREMENTS_FILE)

    print("Parsed Employees:")
    for emp in employees:
        print(emp)

    print("\nParsed Employer Requirements:")
    print(employer_requirements)
