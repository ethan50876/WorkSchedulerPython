from data_manager import Employee, EmployerRequirements, ShiftSchedule, parse_employee_data, parse_employer_requirements
from typing import Dict, List, Tuple, Optional


def is_valid_assignment(
    employee: Employee,
    role: str,
    day: str,
    start_hour: int,
    shift_length: int,
    weekly_assigned_hours: Dict[str, int],
    daily_shifts: Dict[str, List[str]],
    reqs: EmployerRequirements,
) -> bool:
    """Checks if an employee can be assigned a shift while satisfying all constraints."""

    """ Pretty sure these are not needed anymore
    
    print(f"Checking {employee.name} for role {role} on {day} at {start_hour} for {shift_length} hours.")

    if weekly_assigned_hours[employee.name] + shift_length > employee.max_hours:
        print(f"  -> {employee.name} rejected: Exceeds max weekly hours.")
        return False
    
    if start_hour < employee.availability[0] or start_hour + shift_length > employee.availability[1]:
        print(f"  -> {employee.name} rejected: Outside of hourly availability.")

    if day in employee.days_off:
        print(f"  -> {employee.name} rejected: Day off.")
        return False

    if day in daily_shifts.get(employee.name, []):
        print(f"  -> {employee.name} rejected: Already assigned on {day}.")
        return False
    

    
    if start_hour + shift_length > reqs.work_hours[1]:
        print(f"  -> {employee.name} rejected: Shift exceeds store hours.")
        return False
    """

    return True


def meets_critical_minimums_for_day(schedule: ShiftSchedule, reqs: EmployerRequirements, day: str) -> bool:
    """Checks if the schedule meets all role minimums for a specific day."""
    print(f"Validating critical minimums for {day}...")
    for hour, assignments in schedule[day].items():
        role_count = {role: len(assignments.get(role, [])) for role in reqs.critical_minimums.keys()}

        missing_roles = [role for role in reqs.critical_minimums if role_count[role] < reqs.critical_minimums[role]]
        if missing_roles:
            print(f"  -> Shift {day} at {hour}: Missing roles: {', '.join(missing_roles)}")
            return False
    print(f"  -> All shifts for {day} meet critical minimums.")
    return True


def update_schedule(
    employee: Employee,
    role: str,
    day: str,
    start_hour: int,
    shift_length: int,
    schedule: ShiftSchedule,
    weekly_assigned_hours: Dict[str, int],
    daily_shifts: Dict[str, List[str]],
):
    """Assigns an employee to a shift in the schedule."""
    for hour in range(start_hour, start_hour + shift_length):
        if hour not in schedule[day]:
            schedule[day][hour] = {}
        if role not in schedule[day][hour]:
            schedule[day][hour][role] = []
        schedule[day][hour][role].append(employee)

    weekly_assigned_hours[employee.name] += shift_length
    daily_shifts.setdefault(employee.name, []).append(day)
    
    print(f"  -> Assigned {employee.name} to {role} on {day} from {start_hour}:00 to {start_hour + shift_length}:00.")
    
    # Print all employees assigned to the same time block after the assignment
    print(f"  -> Current assignments at {day} {start_hour}:00:")
    for assigned_role, assigned_emps in schedule[day][start_hour].items():
        assigned_emp_names = ', '.join(emp.name for emp in assigned_emps)
        print(f"     - ({assigned_role}): {assigned_emp_names}")



def remove_assignment(
    employee: Employee,
    role: str,
    day: str,
    start_hour: int,
    shift_length: int,
    schedule: ShiftSchedule,
    weekly_assigned_hours: Dict[str, int],
    daily_shifts: Dict[str, List[str]],
):
    """Removes an employee from a shift in the schedule (for backtracking)."""
    for hour in range(start_hour, start_hour + shift_length):
        if role in schedule[day][hour] and employee in schedule[day][hour][role]:
            schedule[day][hour][role].remove(employee)
            if not schedule[day][hour][role]:  # Remove empty lists
                del schedule[day][hour][role]

    weekly_assigned_hours[employee.name] -= shift_length
    daily_shifts[employee.name].remove(day)
    print(f"  -> Backtracking {employee.name} from {role} on {day} at {start_hour}.")


def solve_schedule(
    days: List[str],
    hours: List[int],
    shift_lengths: Tuple[int, int],
    employees: List[Employee],
    reqs: EmployerRequirements,
    schedule: ShiftSchedule,
    weekly_assigned_hours: Dict[str, int],
    daily_shifts: Dict[str, List[str]],
    index: int,
) -> bool:
    """Recursive backtracking function to assign employees to shifts."""
    if index == len(days):

        if all(meets_critical_minimums_for_day(schedule, reqs, day) for day in days):
            print("[Recursion Complete] All critical minimums filled")
            
            """
            # Assign employees to meet minimum hours
            unmet_hours_employees = {emp for emp in employees if weekly_assigned_hours[emp.name] < emp.min_hours}
            
            for employee in unmet_hours_employees:
                if weekly_assigned_hours[employee.name] < shift_lengths[0]:
                    # Try to Extend existing shifts

                else:
                    # Assign new shifts
            """

            return True


    day = days[index]
    print(f"\n--- Processing {day} ---")

    available_employees = {role: [e for e in employees if role in e.roles 
                                  and (day not in e.days_off)
                                  and (day not in daily_shifts.get(e.name, []))]  # Filter out employees already assigned for the day
                                  for role in reqs.critical_minimums}

    for start_hour in sorted(hours):
        print(f"\n--- Assigning shifts for {day} at {start_hour}:00 ---")

        for role in reqs.critical_minimums:
            required_count = reqs.critical_minimums[role]
            assigned_count = len(schedule[day].get(start_hour, {}).get(role, []))

            if assigned_count >= required_count:
                continue  # Role is already fully staffed for this hour

            for _ in range(required_count - assigned_count):  # Try to assign remaining needed employees
                assigned = False
                for employee in [e for e in available_employees.get(role, []) if e.availability[0] <= start_hour]:
                    for shift_length in range(shift_lengths[0], min(shift_lengths[1], 
                                                                    reqs.work_hours[1] - start_hour,
                                                                    employee.availability[1] - start_hour) + 1):
                        
                        """
                        if start_hour + shift_length > reqs.work_hours[1]:
                            continue
                        """

                        if is_valid_assignment(employee, role, day, start_hour, shift_length, weekly_assigned_hours, daily_shifts, reqs):
                            update_schedule(employee, role, day, start_hour, shift_length, schedule, weekly_assigned_hours, daily_shifts)

                            if solve_schedule(days, hours, shift_lengths, employees, reqs, schedule, weekly_assigned_hours, daily_shifts, index):
                                return True

                            remove_assignment(employee, role, day, start_hour, shift_length, schedule, weekly_assigned_hours, daily_shifts)

                if not assigned:
                    print(f"[Backtrack] No valid employee found for {role} on {day} at {start_hour}.")
                    return False

    if not meets_critical_minimums_for_day(schedule, reqs, day):
        return False

    print(f"  -> {day} is fully scheduled. Moving to next day.")
    return solve_schedule(days, hours, shift_lengths, employees, reqs, schedule, weekly_assigned_hours, daily_shifts, index + 1)


def schedule_shifts(employee_file: str, requirements_file: str) -> Optional[ShiftSchedule]:
    """Runs the scheduling process from start to finish."""
    employees = parse_employee_data(employee_file)
    reqs = parse_employer_requirements(requirements_file)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = list(range(reqs.work_hours[0], reqs.work_hours[1]))
    shift_lengths = reqs.shift_lengths

    schedule = {day: {hour: {} for hour in hours} for day in days}
    weekly_assigned_hours = {emp.name: 0 for emp in employees}
    daily_shifts = {}

    solve_schedule(days, hours, shift_lengths, employees, reqs, schedule, weekly_assigned_hours, daily_shifts, 0)

    return schedule if schedule else None


def print_schedule(schedule: ShiftSchedule):
    """Prints the final generated schedule in a readable format."""
    print("\nGenerated Schedule:\n")
    for day, hours in schedule.items():
        print(f"{day}:")
        for hour, roles in sorted(hours.items()):
            assigned_roles = []
            for role, employees in roles.items():
                if isinstance(employees, list):  # Ensure employees are correctly listed
                    for emp in employees:
                        assigned_roles.append(f"({role}) {emp.name}")
                else:
                    assigned_roles.append(f"({role}) {employees.name}")
            print(f"{hour}:00 - {', '.join(assigned_roles)}")
        print()



if __name__ == "__main__":
    EMPLOYEE_FILE = "data/employees.csv"
    REQUIREMENTS_FILE = "data/requirements.csv"

    schedule = schedule_shifts(EMPLOYEE_FILE, REQUIREMENTS_FILE)
    print_schedule(schedule)
