from data_manager import Employee, EmployerRequirements, parse_employee_data, parse_employer_requirements
from typing import Dict, List, Tuple, Optional

# Define ShiftSchedule structure: {Day: {Hour: {Role: Employee}}}
ShiftSchedule = Dict[str, Dict[int, Dict[str, Employee]]]

def is_valid_assignment(employee: Employee, role: str, day: str, start_hour: int, shift_length: int, schedule: ShiftSchedule, weekly_assigned_hours: Dict[str, int], daily_shifts: Dict[str, List[str]], reqs: EmployerRequirements) -> bool:
    """Checks if an employee can be assigned a shift while satisfying all constraints."""
    print(f"Checking {employee.name} for role {role} on {day} at {start_hour} for {shift_length} hours.")

    if weekly_assigned_hours[employee.name] + shift_length > employee.max_hours:
        print(f"  -> {employee.name} rejected: Exceeds max weekly hours.")
        return False

    if day in daily_shifts.get(employee.name, []):
        print(f"  -> {employee.name} rejected: Already assigned on {day}.")
        return False

    if day in employee.days_off:
        print(f"  -> {employee.name} rejected: Day off.")
        return False

    if start_hour < employee.availability[0] or start_hour + shift_length > reqs.work_hours[1]:
        print(f"  -> {employee.name} rejected: Shift exceeds store hours.")
        return False

    for hour in range(start_hour, start_hour + shift_length):
        if hour in schedule[day] and role in schedule[day][hour]:
            print(f"  -> {employee.name} rejected: Role already filled at {hour}.")
            return False

    print(f"  -> {employee.name} assigned successfully.")
    return True

def meets_critical_minimums_for_day(schedule: ShiftSchedule, reqs: EmployerRequirements, day: str) -> bool:
    """Checks if the schedule meets all role minimums for a specific day."""
    print(f"Validating critical minimums for {day}...")
    for hour, assignments in schedule[day].items():
        role_count = {role: 0 for role in reqs.critical_minimums.keys()}
        for role in assignments:
            role_count[role] += 1

        missing_roles = [role for role in reqs.critical_minimums if role_count[role] < reqs.critical_minimums[role]]
        if missing_roles:
            print(f"  -> Shift {day} at {hour}: Missing roles: {', '.join(missing_roles)}")
            return False
    print(f"  -> All shifts for {day} meet critical minimums.")
    return True  

def solve_schedule(days: List[str], hours: List[int], shift_lengths: Tuple[int, int], employees: List[Employee], reqs: EmployerRequirements, schedule: ShiftSchedule, weekly_assigned_hours: Dict[str, int], daily_shifts: Dict[str, List[str]], index: int) -> bool:
    """Recursive backtracking function to assign employees to shifts, ensuring a complete day before moving on."""

    if index == len(days):
        print("[Recursion Complete] All days filled. Validating final critical minimums...")
        return all(meets_critical_minimums_for_day(schedule, reqs, day) for day in days)

    day = days[index]
    available_employees = {role: [e for e in employees if role in e.roles and day not in e.days_off] for role in reqs.critical_minimums}

    for start_hour in sorted(hours):  
        print(f"\n--- Assigning shifts for {day} at {start_hour}:00 ---")

        # Track which roles are already filled at this hour
        assigned_roles = set(schedule[day][start_hour].keys())

        for role in reqs.critical_minimums: 
            if role in assigned_roles:
                continue  # Skip already filled roles

            for shift_length in range(shift_lengths[0], shift_lengths[1] + 1):
                if start_hour + shift_length > reqs.work_hours[1]:
                    continue  # Skip shifts that exceed store closing time

                for employee in available_employees.get(role, []):  
                    if is_valid_assignment(employee, role, day, start_hour, shift_length, schedule, weekly_assigned_hours, daily_shifts, reqs):
                        for hour in range(start_hour, start_hour + shift_length):
                            if hour not in schedule[day]:
                                schedule[day][hour] = {}
                            schedule[day][hour][role] = employee

                        weekly_assigned_hours[employee.name] += shift_length
                        daily_shifts.setdefault(employee.name, []).append(day)

                        print(f"  -> Assigned {employee.name} to {role} on {day} from {start_hour}:00 to {start_hour + shift_length}:00.")

                        # Ensure all roles are filled per hour before moving to the next hour
                        if meets_critical_minimums_for_day(schedule, reqs, day) or solve_schedule(days, hours, shift_lengths, employees, reqs, schedule, weekly_assigned_hours, daily_shifts, index):
                            return True

                        # Backtrack
                        for hour in range(start_hour, start_hour + shift_length):
                            del schedule[day][hour][role]
                        weekly_assigned_hours[employee.name] -= shift_length
                        daily_shifts[employee.name].remove(day)

                        print(f"  -> Backtracking {employee.name} from {role} on {day} at {start_hour}.")

    print(f"[Backtrack] No valid assignment found for {day}. Returning false.")
    return False


def schedule_shifts(employee_file: str, requirements_file: str) -> Optional[ShiftSchedule]:
    employees = parse_employee_data(employee_file)
    reqs = parse_employer_requirements(requirements_file)
    
    # only test Monday - Wednesday for now (keep run time lower)
    days = ["Monday", "Tuesday", "Wednesday"]
    hours = list(range(reqs.work_hours[0], reqs.work_hours[1])) 
    shift_lengths = reqs.shift_lengths

    schedule = {day: {hour: {} for hour in hours} for day in days}
    weekly_assigned_hours = {emp.name: 0 for emp in employees}
    daily_shifts = {}

    if solve_schedule(days, hours, shift_lengths, employees, reqs, schedule, weekly_assigned_hours, daily_shifts, 0):
        return schedule  

    print("[Final] No valid schedule found.")
    return None  

def print_schedule(schedule: Optional[ShiftSchedule]):
    if schedule is None:
        print("No valid schedule found.")
        return  

    print("\nGenerated Schedule:")
    for day, shifts in schedule.items():
        print(f"\n{day}:")
        for hour, assignments in shifts.items():
            assigned_roles = [f"({role}){emp.name}" for role, emp in assignments.items()]
            print(f"{hour}:00 - {', '.join(assigned_roles)}")

if __name__ == "__main__":
    EMPLOYEE_FILE = "data/employees.csv"
    REQUIREMENTS_FILE = "data/requirements.csv"

    schedule = schedule_shifts(EMPLOYEE_FILE, REQUIREMENTS_FILE)

    print_schedule(schedule)
