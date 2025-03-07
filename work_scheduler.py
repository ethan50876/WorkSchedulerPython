from data_manager import Employee, EmployerRequirements, parse_employee_data, parse_employer_requirements
from typing import Dict, List, Tuple, Optional
import sys

# {day: {hour: {role: [Employee]}}}
ShiftSchedule = Dict[str, Dict[int, Dict[str, List[Employee]]]]

def is_valid_assignment(
    employee: Employee,
    role: str,
    day: str,
    start_hour: int,
    shift_length: int,
    weekly_assigned_hours: Dict[str, int], # {employee_name: hours_assigned}
    daily_shifts: Dict[str, List[str]], # {employee_name: [days_assigned]}
    reqs: EmployerRequirements,
) -> bool:
    """
    Checks if an employee can be assigned a shift while satisfying all constraints.
    Args:
        employee (Employee): The employee to be assigned the shift.
        role (str): The role the employee will be assigned to.
        day (str): The day of the week for the shift.
        start_hour (int): The starting hour of the shift (24-hour format).
        shift_length (int): The length of the shift in hours.
        weekly_assigned_hours (Dict[str, int]): A dictionary mapping employee names to their current total weekly hours.
        daily_shifts (Dict[str, List[str]]): A dictionary mapping employee names to the list of days they are assigned shifts.
        reqs (EmployerRequirements): The employer's requirements including work hours and other constraints.
    Returns:
        bool: True if the assignment is valid, False otherwise.
    """
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

    if start_hour < employee.availability[0] or start_hour + shift_length > reqs.work_hours[1] or start_hour + shift_length > employee.availability[1]:
        print(f"  -> {employee.name} rejected: Shift exceeds store hours.")
        return False

    return True


def meets_critical_minimums_for_day(schedule: ShiftSchedule, reqs: EmployerRequirements, day: str) -> bool:
    """
    Checks if the schedule meets all role minimums for a specific day.
    Args:
        schedule (ShiftSchedule): The schedule containing assignments for each day and hour.
        reqs (EmployerRequirements): The requirements specifying the critical minimums for each role.
        day (str): The specific day to check the schedule for.
    Returns:
        bool: True if all shifts for the specified day meet the critical minimums, False otherwise.
    """
 
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
    """
    Assigns an employee to a shift in the schedule.
    Args:
        employee (Employee): The employee to be assigned to the shift.
        role (str): The role the employee will be performing during the shift.
        day (str): The day of the week for the shift (e.g., 'Monday').
        start_hour (int): The starting hour of the shift (24-hour format).
        shift_length (int): The length of the shift in hours.
        schedule (ShiftSchedule): The current shift schedule.
        weekly_assigned_hours (Dict[str, int]): A dictionary tracking the total hours assigned to each employee for the week.
        daily_shifts (Dict[str, List[str]]): A dictionary tracking the days each employee is assigned to work.
    Prints to log:
        A message indicating the assignment of the employee to the shift.
        A message listing all employees assigned to the same time block after the assignment.
    """

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
    """
    Removes an employee from a shift in the schedule (used for backtracking).
    Args:
        employee (Employee): The employee to be removed from the shift.
        role (str): The role assigned to the employee.
        day (str): The day of the shift.
        start_hour (int): The starting hour of the shift.
        shift_length (int): The length of the shift in hours.
        schedule (ShiftSchedule): The current shift schedule.
        weekly_assigned_hours (Dict[str, int]): A dictionary tracking the weekly assigned hours for each employee.
        daily_shifts (Dict[str, List[str]]): A dictionary tracking the days each employee is assigned to shifts.
    Returns:
        None
    """

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
    """
    Recursive backtracking function to assign employees to shifts.
    Args:
        days (List[str]): List of days to schedule that is iterated over recursively.
        hours (List[int]): List of hours in a day to consider for shifts.
        shift_lengths (Tuple[int, int]): Minimum and maximum shift lengths.
        employees (List[Employee]): List of Employee objects available for scheduling.
        reqs (EmployerRequirements): Object containing employer's requirements including critical minimums and work hours.
        schedule (ShiftSchedule): Current shift schedule being built.
        weekly_assigned_hours (Dict[str, int]): Dictionary tracking total weekly hours assigned for each employee.
        daily_shifts (Dict[str, List[str]]): Dictionary tracking days worked for each employee, {employee_name: [days]}.
        index (int): Current index in the days list being processed.
    Returns:
        bool: True if a valid schedule is found, False otherwise.
    """
    if index == len(days):
        print("[Recursion Complete] All days filled. Validating final critical minimums...")
        return all(meets_critical_minimums_for_day(schedule, reqs, day) for day in days)

    day = days[index]
    print(f"\n--- Processing {day} ---")

    available_employees = {role: [e for e in employees if role in e.roles and day not in e.days_off] for role in reqs.critical_minimums}

    for start_hour in sorted(hours):
        print(f"\n--- Assigning shifts for {day} at {start_hour}:00 ---")

        for role in reqs.critical_minimums:
            required_count = reqs.critical_minimums[role]
            assigned_count = len(schedule[day].get(start_hour, {}).get(role, []))

            if assigned_count >= required_count:
                continue  # Role is already fully staffed for this hour

            for _ in range(required_count - assigned_count):  # Try to assign remaining needed employees
                assigned = False
                for employee in available_employees.get(role, []):
                    for shift_length in range(shift_lengths[0], shift_lengths[1] + 1):
                        if start_hour + shift_length > reqs.work_hours[1]:
                            continue

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


def assign_extra_shifts(
    schedule: ShiftSchedule,
    employees: List[Employee],
    reqs: EmployerRequirements,
    weekly_assigned_hours: Dict[str, int],
    daily_shifts: Dict[str, List[str]]
):
    """
    Ensures that all employees meet their minimum hours by assigning extra shifts as 'Floater'.
    Distributes extra shifts evenly so that the least staffed day is not 50% less than any other day.
    Exception: if the employee's hours remaining are less than the minimum shift length, they will not be assigned.
    Args:
        schedule (ShiftSchedule): The current shift schedule.
        employees (List[Employee]): List of employees to be scheduled.
        reqs (EmployerRequirements): Requirements set by the employer, including work hours and shift lengths.
        weekly_assigned_hours (Dict[str, int]): Dictionary mapping employee names to their currently assigned weekly hours.
        daily_shifts (Dict[str, List[str]]): Dictionary mapping employee names to their assigned shifts per day.
    Returns:
        None
    """

    print("\nAssigning extra shifts to under-scheduled employees...")
    under_min_hours = [emp for emp in employees if weekly_assigned_hours[emp.name] < emp.min_hours]
    
    # Calculate initial employee count per day
    day_counts = {day: sum(len(roles) for roles in schedule[day].values()) for day in schedule.keys()}
    sorted_days = sorted(schedule.keys(), key=day_counts.get)
    
    for employee in under_min_hours:
        required_hours = employee.min_hours - weekly_assigned_hours[employee.name]
        print(f"\nFinding extra shifts for {employee.name} (Needs {required_hours} more hours)")
        
        for least_scheduled_day in sorted_days:
            if required_hours <= 0:
                break  # Stop assigning if min hours are met
            
            if least_scheduled_day in employee.days_off or least_scheduled_day in daily_shifts.get(employee.name, []):
                continue  # Skip if the employee has a day off or is already assigned
            
            for hour in range(reqs.work_hours[0], reqs.work_hours[1]):
                if required_hours <= 0:
                    break
                
                role = "Floater"  # Override role to 'Floater'
                shift_length = reqs.shift_lengths[0]  # Assign the shortest possible shift
                
                if is_valid_assignment(
                    employee, role, least_scheduled_day, hour, shift_length,
                    weekly_assigned_hours, daily_shifts, reqs
                ):
                    update_schedule(
                        employee, role, least_scheduled_day, hour, shift_length,
                        schedule, weekly_assigned_hours, daily_shifts
                    )
                    required_hours -= shift_length
                    day_counts[least_scheduled_day] += 1  # Update the day count
    
    print("\n[Adjustment Complete] All employees should now meet their minimum hours and schedule is balanced.")



def schedule_shifts(employee_file: str, requirements_file: str) -> Optional[ShiftSchedule]:
    """
    Runs the scheduling process from start to finish.
    Args:
        employee_file (str): Path to the file containing employee data.
        requirements_file (str): Path to the file containing employer requirements.
    Returns:
        Optional[ShiftSchedule]: A dictionary representing the shift schedule if successful, 
        otherwise None.
    """
    employees = parse_employee_data(employee_file)
    reqs = parse_employer_requirements(requirements_file)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = list(range(reqs.work_hours[0], reqs.work_hours[1]))
    shift_lengths = reqs.shift_lengths

    schedule = {day: {hour: {} for hour in hours} for day in days}
    weekly_assigned_hours = {emp.name: 0 for emp in employees}
    daily_shifts = {}

    # Redirect print output to debug.txt
    original_stdout = sys.stdout
    with open("output/debug.txt", "w") as debug_log:
        sys.stdout = debug_log
        
        if solve_schedule(days, hours, shift_lengths, employees, reqs, schedule, weekly_assigned_hours, daily_shifts, 0):
            assign_extra_shifts(schedule, employees, reqs, weekly_assigned_hours, daily_shifts)
        else:
            schedule = None

    # Restore normal print output after schedule generation
    sys.stdout = original_stdout
    
    return schedule if schedule else None


def print_schedule(schedule: ShiftSchedule, output_file: str):
    """
    Writes the final generated schedule to a file.

    Args:
        schedule (ShiftSchedule): A dictionary representing the schedule.
                                  {day: {hour: {role: [Employee]}}}

        output_file (str): The path to the file where the schedule will be written.
    """
    with open(output_file, "w") as schedule_file:
        schedule_file.write("\nGenerated Schedule:\n\n")
        for day, hours in schedule.items():
            schedule_file.write(f"{day}:\n")
            for hour, roles in sorted(hours.items()):
                assigned_roles = []
                for role, employees in roles.items():
                    if isinstance(employees, list):
                        for emp in employees:
                            assigned_roles.append(f"({role}) {emp.name}")
                    else:
                        assigned_roles.append(f"({role}) {employees.name}")
                schedule_file.write(f"{hour}:00 - {', '.join(assigned_roles)}\n")
            schedule_file.write("\n")

if __name__ == "__main__":
    """
    Main function:
        - Defines filepaths
        - Calls schedule_shifts
        - Calls print_schedule or outputs error message
    """

    EMPLOYEE_FILEPATH = "data/impossibleEmps3.csv"
    REQUIREMENTS_FILEPATH = "data/validReqs1.csv"
    OUTPUT_FILEPATH = "output/"

    schedule = schedule_shifts(EMPLOYEE_FILEPATH, REQUIREMENTS_FILEPATH)

    def extract_filename(filepath: str) -> str:

        return filepath.split('/')[-1].split('.')[0]

    employeeFilename = extract_filename(EMPLOYEE_FILEPATH)
    requirementsFilename = extract_filename(REQUIREMENTS_FILEPATH)

    if schedule != None:
        print_schedule(schedule, OUTPUT_FILEPATH + f"{employeeFilename}_{requirementsFilename}_schedule.csv")
        print("Schedule generation complete. Output saved to 'output/' directory.")
    else:
        print("Error: Schedule generation failed. Check 'output/debug.txt' for details.")
