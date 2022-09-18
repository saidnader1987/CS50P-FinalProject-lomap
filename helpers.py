from functools import reduce
from datetime import date
from dateutil.relativedelta import relativedelta
import csv

from pyfiglet import Figlet
from tabulate import tabulate


# Constants
MONTHS = {
    "monthly": 1,
    "bi-monthly": 2,
    "quarterly": 3,
    "semi-annually": 6,
    "annually": 12
}

PERIODS = {
    "monthly": 12,
    "bi-monthly": 6,
    "quarterly": 4,
    "semi-annually": 2,
    "annually": 1
}

TYPES = ["effective", "nominal"]


# Functions
def check_frequency(term, frequency):
    """
    Input: term, an int specifying the number of months of one loan
    Input: frequency, a string specifying the payment frequency
    Returns True if the frequency exists in the PERIODS dict and match the term, otherwise False
    """
    if frequency == "at maturity":
        return True
    # frequency exists
    elif frequency.lower() in PERIODS:
        # months in frequency period
        period = MONTHS[frequency.lower()]
        # term is divisible by period
        if term % period == 0:
            return True
        else:
            return False
    else:
        return False


def get_obj(l, v, lookup_att):
    """
    Input: l, a list of objects
    Input: v, the value of an attribute of the object
    Input: lookup_att, the name of the attribute of the object
    Returns obj if the object is found, otherwise None
    """
    for obj in l:
        if getattr(obj, lookup_att) == v:
            return obj
    return None


def message_to_figlet(message, font):
    """
    Input: message, a message string to render
    Input: font, must be a validate figlet font (http://www.figlet.org/examples.html)
    Renders text in figlet font
    """
    figlet = Figlet()
    figlet.setFont(font = font)
    # figlet.setFont(font = "doom")
    print(f"{figlet.renderText(message)}")


def generate_amortizations(face, term, issue, frequency):
    amortizations = {}
    # calculate amortization periods
    # if frequency != "at maturity":
    #     n = term / MONTHS[frequency]
    # else:
    #     n = 1
    n = term / MONTHS[frequency] if frequency != "at maturity" else 1
    # calculate scheduled amortizations
    sch_amort = round(face / n, 2)
    for i in range(term):
        # generate monthly periods
        date_i = issue + relativedelta(months=i + 1)
        # checking if period divided by MONTHS has a remainder
        if frequency != "at maturity" and (i + 1) % MONTHS[frequency] == 0:
            amortizations[date_i] = sch_amort
        elif frequency == "at maturity" and i + 1 == term:
            amortizations[date_i] = sch_amort
        else:
            amortizations[date_i] = 0
    return amortizations


def generate_actual_amortization_schedule(issue, sch_amortizations, actual_amortizations, principal, sch_principals_a_amort):
    # getting loan term
    term = len(sch_amortizations)
    # getting loan issue_date
    # issue = min(sch_amortizations) + relativedelta(months=- 1)
    # Creating the dict that will be returned
    actual_amortization_schedule = {}
    actual_amortizations_dict = {}
    # getting remaining periods, number of amortizations and future amortization value
    # max_amort_date = max(actual_amortizations, key = lambda x : x.amort_date).amort_date
    # generating all periods
    check = False
    today = date.today()
    last_date = max(sch_amortizations)

    if today < last_date:
        for i in range(term):
            date_i = issue + relativedelta(months=i + 1)
            date_i_minus_1 = issue + relativedelta(months = i)
            # date_i_minus_1 = date_i + relativedelta(months= - 1)
            actual_amort_in_period = sum(amort.value for amort in actual_amortizations if amort.amort_date > date_i_minus_1
            and amort.amort_date <= date_i)
            # Period less than today
            if date_i_minus_1 < today and date_i < today:
                actual_amortization_schedule[date_i] = actual_amort_in_period
                actual_amortizations_dict[date_i] = actual_amort_in_period
            # Period == today
            elif date_i_minus_1 < today <= date_i:
                # actual_amort_in_period = sum(amort.value for amort in actual_amortizations if amort.amort_date > date_i_minus_1
                # and amort.amort_date <= date_i)
                # Checking to see if there's a scheduled amortization in period
                # Period is not an amortization payment month
                if round(sch_amortizations[date_i],0) == 0:
                    actual_amortization_schedule[date_i] = actual_amort_in_period
                    actual_amortizations_dict[date_i] = actual_amort_in_period
                # Amortization payment month
                else:
                    # Must meet condition that actual principal == scheduled principal
                    due = round(principal - sch_principals_a_amort[date_i], 1)
                    if due > 0 and check == False:
                        actual_amortization_schedule[date_i] = actual_amort_in_period + due
                        actual_amortizations_dict[date_i] = actual_amort_in_period
                        check = True
                    else:
                        actual_amortization_schedule[date_i] = actual_amort_in_period
                        actual_amortizations_dict[date_i] = actual_amort_in_period
            # Period is greater than today
            elif today <= date_i_minus_1:
                if not check:
                    due = round(principal - sch_principals_a_amort[date_i], 1)
                     # Checking to see if there's a scheduled amortization in period
                    # Period is not an amortization payment month
                    if round(sch_amortizations[date_i],0) == 0:
                        actual_amortization_schedule[date_i] = actual_amort_in_period
                    else:
                        if due > 0:
                            actual_amortization_schedule[date_i] = due
                            check = True
                        elif due <= 0:
                            actual_amortization_schedule[date_i] = 0
                else:
                    actual_amortization_schedule[date_i] = sch_amortizations[date_i]
                actual_amortizations_dict[date_i] = 0
    else:
        for i in range(term):
            date_i = issue + relativedelta(months=i + 1)
            date_i_minus_1 = issue + relativedelta(months = i)
            actual_amort_in_period = sum(amort.value for amort in actual_amortizations if amort.amort_date > date_i_minus_1
            and amort.amort_date <= date_i)
            # Period differente than last period
            if i != term - 1:
                actual_amortization_schedule[date_i] = actual_amort_in_period
                actual_amortizations_dict[date_i] = actual_amort_in_period
            else:
                # due = round(principal - sch_principals_a_amort[date_i], 1)
                actual_amortization_schedule[date_i] = principal
                actual_amortizations_dict[date_i] = actual_amort_in_period
    return actual_amortization_schedule, actual_amortizations_dict


# def generate_actual_amortization_schedule(sch_amortizations, actual_amortizations, principal, sch_principals_a_amort):
#     # getting loan term
#     term = len(sch_amortizations)
#     # getting loan issue_date
#     issue = min(sch_amortizations) + relativedelta(months=- 1)
#     # Creating the dict that will be returned
#     actual_amortization_schedule = {}
#     actual_amortizations_dict = {}
#     # getting remaining periods, number of amortizations and future amortization value
#     max_amort_date = max(actual_amortizations, key = lambda x : x.amort_date).amort_date
#     # generating all periods
#     check = False
#     for i in range(term):
#         date_i = issue + relativedelta(months=i + 1)
#         date_i_minus_1 = date_i + relativedelta(months= - 1)
#         # Period less than period where max_amort_date is
#         if date_i_minus_1 < max_amort_date and date_i < max_amort_date:
#             actual_amort_in_period = sum(amort.value for amort in actual_amortizations if amort.amort_date > date_i_minus_1
#             and amort.amort_date <= date_i)
#             actual_amortization_schedule[date_i] = actual_amort_in_period
#             actual_amortizations_dict[date_i] = actual_amort_in_period
#         # Period == max_amort_date
#         elif date_i_minus_1 < max_amort_date <= date_i:
#             actual_amort_in_period = sum(amort.value for amort in actual_amortizations if amort.amort_date > date_i_minus_1
#             and amort.amort_date <= date_i)
#             # Checking to see if there's a scheduled amortization in period
#             # Period is not an amortization payment month
#             if sch_amortizations[date_i] == 0:
#                 actual_amortization_schedule[date_i] = actual_amort_in_period
#                 actual_amortizations_dict[date_i] = actual_amort_in_period
#             # Amortization payment month
#             else:
#                 # Must meet condition that actual principal == scheduled principal
#                 due = round(principal - sch_principals_a_amort[date_i], 1)
#                 if due > 0 and check == False:
#                     actual_amortization_schedule[date_i] = actual_amort_in_period + due
#                     actual_amortizations_dict[date_i] = actual_amort_in_period
#                     check = True
#                 else:
#                     actual_amortization_schedule[date_i] = actual_amort_in_period
#                     actual_amortizations_dict[date_i] = actual_amort_in_period
#         # Period is greater than max_amort_date
#         elif max_amort_date <= date_i_minus_1:
#             if not check:
#                 due = round(principal - sch_principals_a_amort[date_i], 1)
#                 if due > 0:
#                     actual_amortization_schedule[date_i] = due
#                     check = True
#                 elif due <= 0:
#                     actual_amortization_schedule[date_i] = 0
#             else:
#                 actual_amortization_schedule[date_i] = sch_amortizations[date_i]
#             actual_amortizations_dict[date_i] = 0
#     return actual_amortization_schedule, actual_amortizations_dict


def generate_principals(face, term, cash_flow, issue):
    principals_a = {}
    principals_b = {}
    principal = face
    for i in range(term):
        date_i = issue + relativedelta(months=i + 1)
        sch_amort = cash_flow[date_i]
        principal -= sch_amort
        principals_a[date_i] = round(principal, 2)
        principals_b[date_i] = round(principal + sch_amort, 2)
    return principals_b , principals_a


def generate_interests(cash_flow, rate, comp_period, frequency, issue):
# def generate_interests(rate, period):
    interests = {}
    # calculate monthly rate
    i_m = convert_nominal_to_monthly_effective(rate, comp_period)
    acc_interest = 0
    # calculate months until interest payment
    n = MONTHS[frequency] if (frequency != "at maturity") else len(cash_flow)
    for i in range(len(cash_flow)):
        # generate monthly periods
        date_i = issue + relativedelta(months=i + 1)
        # calculate monthly interest
        interest_m = calculate_interest(i_m, cash_flow[date_i])
        # future value of monthly interest at payment date
        comp_periods_i = (n - (i + 1) % n) if (i + 1) % n != 0 else 0
        fv_interest_m = interest_m * (1 + i_m / 100) ** comp_periods_i
        # accrued interest
        acc_interest += fv_interest_m
        if frequency != "at maturity" and (i + 1) % MONTHS[frequency] == 0:
            interests[date_i] = round(acc_interest, 2)
            acc_interest = 0
        elif frequency == "at maturity" and i + 1 == len(cash_flow):
            interests[date_i] = round(acc_interest, 2)
        else:
            interests[date_i] = 0
    return interests


def convert_nominal_to_monthly_effective(rate, comp_period):
    nominal_comp_periods = PERIODS[comp_period]
    # calculate the effective rate according to the compounding periods of nominal rate
    effective_rate = (rate / nominal_comp_periods)
    # calculate effective monthly rate
    effective_monthly_rate = ((1 + effective_rate / 100) ** (1/MONTHS[comp_period]) - 1)
    return round(effective_monthly_rate * 100, 4)


def calculate_interest(rate:float, value:float) -> float:
    return round(rate * value / 100, 2)

def calculate_principal_balance(face:float, am_list:list)->float:
    if len(am_list) > 1:
        am = reduce(lambda a, b: a + b, am_list)
        return face - am
    elif len(am_list) == 1:
        return face - am_list[0].value
    else:
        return face


def loans_report(loans):
    if len(loans) != 0:
        table = []
        # wrapper = textwrap.TextWrapper(width=50)
        headers = [
            "ID",
            "Face Value",
            "Principal",
            "Bank",
            "Issue Date",
            "Term",
            "Payment\nFreq.",
            "Int. Rate",
            "Int. Rate\nType",
            "Rate Comp.\nPeriod",
            "Int. Payment\nFreq."
        ]

        for loan in loans:
            loan_info = [
                loan.id,
                f"${loan.face_value:,.1f}",
                f"${loan.principal_balance:,.1f}",
                loan.bank.bank,
                loan.issue_date,
                loan.loan_term,
                loan.payment_frequency.title(),
                f"{loan.interest_rate:.2f}%",
                loan.interest_rate_type.title(),
                loan.nominal_rate_compounding_period.title(),
                loan.interest_payment_frequency.title()
            ]
            table.append(loan_info)
        print(tabulate(table, headers, tablefmt="pretty", colalign=("right", "right", "right", "center", "right", "right", "center", "right", "center", "center", "center")))
    else:
        print("Loans database is empty")
        return True

def amort_report(amortizations):
    if len(amortizations) != 0:
        table = []
        # wrapper = textwrap.TextWrapper(width=50)
        headers = [
            "ID",
            "Loan ID",
            "Value",
            "Date"
        ]

        for amortization in amortizations:
            amort_info = [
                amortization.id,
                amortization.loan_id,
                f"${amortization.value:,.1f}",
                amortization.amort_date
            ]
            table.append(amort_info)
        print(tabulate(table, headers, tablefmt="pretty", colalign=("right", "right", "right", "center")))
    else:
        print("Amortizations database is empty")
        return True


def banks_report(banks):
    if len(banks) != 0:
        table = []
        # wrapper = textwrap.TextWrapper(width=50)
        headers = [
            "ID",
            "Bank",
        ]

        for bank in banks:
            bank_info = [
                bank.id,
                bank.bank,
            ]
            table.append(bank_info)
        print(tabulate(table, headers, tablefmt="pretty", colalign=("right", "center")))
    else:
        print("Banks database is empty")
        return True


def print_frequencies():
    table = []
    headers = [
        "Frequency"
    ]

    for frequency in MONTHS.keys():
        frequency_info = [
            frequency
        ]
        table.append(frequency_info)
    print(tabulate(table, headers, tablefmt="pretty"))


def print_types():
    table = []
    headers = [
        "Interest Rate Type"
    ]

    for type in TYPES:
        types_info = [
            type
        ]
        table.append(types_info)
    print(tabulate(table, headers, tablefmt="pretty"))


def print_periods():
    table = []
    headers = [
        "Nominal Rate Compounding Period"
    ]

    for period in PERIODS:
        period_info = [
            period
        ]
        table.append(period_info)
    print(tabulate(table, headers, tablefmt="pretty"))


def cash_flow_report(loan):
    table = []
    # wrapper = textwrap.TextWrapper(width=50)
    headers = [
        "Date",
        "Scheduled\nPrincipal\nBefore\nAmortization",
        "Sccheduled\nAmortization",
        "Scheduled\nInterest",
        "Actual\nPrincipal\nBefore\nAmortization",
        "Actual\nAmortization",
        "Actual\nAmortization\nSchedule",
        "Actual\nInterest\nSchedule",
    ]

    for period in loan.amort_schedule:
        cash_flow_info = [
            period,
            f"${loan.scheduled_principals_b_amort[period]:,.1f}",
            f"${loan.amort_schedule[period]:,.1f}",
            f"${loan.interest_payment_schedule[period]:,.1f}",
            f"${loan.actual_principals_b_amort[period]:,.1f}", #if len(loan.actual_amortizations) != 0 else
            #f"${loan.scheduled_principals_b_amort[period]:,.1f}",
            f"${loan.actual_amortizations_dict[period]:,.1f}", #if len(loan.actual_amortizations) != 0 else
            #f"${0:,.1f}",
            f"${loan.actual_amort_schedule[period]:,.1f}", #if len(loan.actual_amortizations) != 0 else
            #f"${loan.amort_schedule[period]:,.1f}",
            f"${loan.actual_interest_payment_schedule[period]:,.1f}", #if len(loan.actual_amortizations) != 0 else
            #f"${loan.interest_payment_schedule[period]:,.1f}"
        ]
        table.append(cash_flow_info)
    print(tabulate(table, headers, tablefmt="pretty", colalign=("center", "right", "right", "right", "right", "right", "right", "right")))


def write_csv_file(path, fields, entries):
    with open(path, "w") as file:
        writer = csv.DictWriter(file, fields)
        writer.writeheader()
        for entry in entries:
            att_array = str(entry).split(",")
            att_dict = dict(zip(fields, att_array))
            writer.writerow(att_dict)


def append_csv_file(path, fields, entry):
    att_array = str(entry).split(",")
    att_dict = dict(zip(fields, att_array))
    with open(path, "a") as file:
        writer = csv.DictWriter(file, fields)
        writer.writerow(att_dict)
    print("Data saved")


