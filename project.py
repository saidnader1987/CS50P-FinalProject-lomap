import csv
import sys
from pathlib import Path
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from helpers import MONTHS, PERIODS, TYPES, check_frequency, get_obj, \
    message_to_figlet, generate_amortizations, generate_interests, generate_principals, \
    calculate_principal_balance, generate_actual_amortization_schedule, loans_report, amort_report, \
    banks_report, print_frequencies, print_types, print_periods, cash_flow_report, append_csv_file, \
    write_csv_file


banks = []
amortizations = []
loans = []

LOAN_FIELDS = [
    "id",
    "face_value",
    "bank",
    "issue_date",
    "loan_term",
    "payment_frequency",
    "interest_rate",
    "interest_rate_type",
    "nominal_rate_compounding_period",
    "interest_payment_frequency"
]

AMORTIZATION_FIELDS = [
    "id",
    "loan_id",
    "value",
    "amort_date"
]

BANK_FIELDS = [
    "id",
    "bank"
]

# getting current working directory and defining database paths
cwd = Path.cwd()
bank_path = 'data/banks.csv'
loans_path = 'data/loans.csv'
amort_path = 'data/amortizations.csv'

# Bank class


class Bank:
    def __init__(self, id, bank):
        self.id = id
        self.bank = bank

    # Setting properties
    # id: Can only be set the first time the object is constructed
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        if not hasattr(self, 'id'):
            self._id = int(id)
        else:
            raise ValueError("Can't change id manually")

    # bank
    @property
    def bank(self):
        return self._bank

    # setter
    @bank.setter
    def bank(self, bank):
        # if bank.lower().title() not in banks:
        if len(banks) != 0 and any(obj.bank == bank.lower().title() for obj in banks):
            raise ValueError(
                "Invalid input: Bank already exists in the database.")
        self._bank = bank.lower().title()

     # str method: returns csv-like string
    def __str__(self):
        return f"{self.id},{self.bank}"

    def edit(self):
        print("Please enter the following data. At any moment press CTRL + D to go back to the previous menu without saving.")
        # input for bank
        old_bank = self.bank
        while True:
            if new_bank := input("Bank: ").lower().title():
                # if bank already in database:
                if len(banks) != 0 and any(obj.bank == new_bank.lower().title() for obj in banks):
                    print(
                        "Invalid input: Bank already exists in the database. Banks in database:")
                    banks_report(banks)
                    continue
                else:
                    break
        # Change bank in banks array
        self.bank = new_bank
        # # Change bank in every loan in loans array
        # update_object(loans, "bank", old_bank, new_bank)
        # Writing csv file
        write_csv_file(cwd / bank_path, BANK_FIELDS, banks)
        write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
        print("Data saved")

    def delete(self):
        # if bank already in use in loans:
        if any(obj.bank.bank == self.bank.lower().title() for obj in loans):
            print("Bank can not be deleted because it has loans associated with it")
        else:
            # delete bank from banks list
            banks.remove(self)
            # update csv
            write_csv_file(cwd / bank_path, BANK_FIELDS, banks)
            print("Bank deleted")

    # def __del__(self):
    #     print("Im am deleted")

    # class method for users registering banks

    @classmethod
    def get(cls):
        # Must validate user's input in each step, so that the user does not have to start at the beginning each time his input is invalid
        # id assigned automatically: last bank in banks (banks is sorted)
        if len(banks) != 0:
            id = banks[-1].id + 1
        else:
            id = 1
        print("Please enter the following data. At any moment press CTRL + D to go back to the previous menu without saving.")
        # input for bank
        while True:
            if bank := input("Bank: ").lower().title():
                # if bank already in database:
                if len(banks) != 0 and any(obj.bank == bank.lower().title() for obj in banks):
                    print(
                        "Invalid input: Bank already exists in the database. Banks in database:")
                    banks_report(banks)
                    continue
                else:
                    break

        return cls(id, bank)


# Amortization class
class Amortization:
    def __init__(self, id, loan_id, value, amort_date):
        # , value, date):
        self.id = id
        self.loan_id = loan_id
        self.value = value
        self.amort_date = amort_date

    # Setting properties
    # id: Can only be set the first time the object is constructed
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        if not hasattr(self, 'id'):
            self._id = int(id)
        else:
            raise ValueError("Can't change id manually")

    # loan_id
    @property
    def loan_id(self):
        return self._loan_id

    # setter
    @loan_id.setter
    def loan_id(self, loan_id):
        # if loan_id not in loans
        if not any(str(obj.id) == str(loan_id) for obj in loans):
            raise ValueError(f"No loan with id: {loan_id} in database")
        self._loan_id = int(loan_id)

    # value: must be an integer or a float and sum of values must add up to face_value
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        try:
            value = float(value)
            if value < 0:
                raise ValueError
        except ValueError:
            raise ValueError("Amortization value must be a positive number")
        else:
            # if value <= 0:
            #     raise ValueError("Amortization value must be a positive number")
            loan = get_obj(loans, self.loan_id, "id")
            loan_principal_balance = loan.principal_balance
            if value > loan_principal_balance:
                raise ValueError(
                    f"Amortization value (${value:,.2f}) can not be greater than loan balance (${loan_principal_balance:,.2f})")
            self._value = value

    # amort_date: must be a valid date and between issue date and date at maturity
    @property
    def amort_date(self):
        return self._amort_date

    @amort_date.setter
    def amort_date(self, amort_date):
        if not isinstance(amort_date, date):
            try:
                amort_date = datetime.strptime(amort_date, '%Y-%m-%d').date()
            except ValueError:
                print("Invalid date format, should be YYYY-MM-DD")
        loan = get_obj(loans, self.loan_id, "id")
        loan_issue_date = loan.issue_date
        loan_term = loan.loan_term
        loan_maturity = loan_issue_date + relativedelta(months=loan_term)
        today = date.today()
        if not amort_date <= today:
            raise ValueError(
                f"Amortization date ({str(amort_date)}) can not be greater than today ({str(today)})")
        if not loan_issue_date < amort_date <= loan_maturity:
            raise ValueError(
                f"Amortization date ({str(amort_date)}) can not be less than or equal to loan issue date ({str(loan_issue_date)}) and can not be greater than loan maturity date ({str(loan_maturity)})")
        self._amort_date = amort_date

     # str method: returns csv-like string
    def __str__(self):
        return f"{self.id},{self.loan_id},{self.value},{str(self.amort_date)}"

    # adding 2 amortizations or 1 amortization plus a float
    # self + other
    def __add__(self, other):
        try:
            other = float(other)
        except TypeError:
            return self.value + other.value
        else:
            return self.value + other

    # other + self
    def __radd__(self, other):
        try:
            other = float(other)
        except TypeError:
            return other.value + self.value
        else:
            return other + self.value

    def edit(self):
        while True:
            # print("Please enter the following data. At any moment press CTRL + D to go back to the previous menu without saving.")
            option = input(
                "Choose an option to edit: (v)alue, (a)mortization date: ").lower()
            # input for value
            if option == "v":
                old_value = self.value
                while True:
                    if new_value := input("Amortization value: "):
                        try:
                            new_value = float(new_value)
                            if new_value <= 0:
                                raise ValueError
                        except ValueError:
                            print(
                                "Invalid input: Amortization value must be a positive number")
                            continue
                        else:
                            loan = get_obj(loans, self.loan_id, "id")
                            loan_principal_balance = loan.principal_balance
                            if new_value > loan_principal_balance + old_value:
                                print(f"Amortization value (${new_value:,.2f}) must be less than or equal to loan balance plus",
                                      f"the old amortization value (${loan_principal_balance + old_value:,.2f})")
                                continue
                            else:
                                break
                # Change amort in amortizations array
                self.value = 0
                loan.update_balance()
                self.value = new_value
                write_csv_file(cwd / amort_path,
                               AMORTIZATION_FIELDS, amortizations)
                loan.update_act()
                print("Data saved")
                break
            elif option == "a":
                # old_date = self.amort_date
                while True:
                    if new_date := input("Amortization date: "):
                        try:
                            new_date = datetime.strptime(
                                new_date, '%Y-%m-%d').date()
                        except ValueError:
                            print("Invalid date format, should be YYYY-MM-DD")
                            continue
                        else:
                            loan = get_obj(loans, self.loan_id, "id")
                            loan_issue_date = loan.issue_date
                            loan_term = loan.loan_term
                            loan_maturity = loan_issue_date + \
                                relativedelta(months=loan_term)
                            today = date.today()
                            if not new_date <= today:
                                print(
                                    f"Amortization date ({str(new_date)}) can not be greater than today ({str(today)})")
                                continue
                            elif not loan_issue_date < new_date <= loan_maturity:
                                print(
                                    f"Amortization date ({str(new_date)}) can not be less than or equal to loan issue date ({str(loan_issue_date)}) and can not be greater than loan maturity date ({str(loan_maturity)})")
                                continue
                            else:
                                break
                # Change amort in amortizations array
                self.amort_date = new_date
                write_csv_file(cwd / amort_path,
                               AMORTIZATION_FIELDS, amortizations)
                loan.update_act()
                print("Data saved")
                break
            else:
                print(
                    "Invalid input. Usage: v for editing amortization value, a for editing amortization date")
                continue

    def delete(self):
        # delete amortization in loan
        # get loan based on amortization.loan_id and add amortization
        loan = get_obj(loans, int(self.loan_id), "id")
        loan.actual_amortizations.remove(self)
        loan.update_act()
        # delete amortization itself
        amortizations.remove(self)
        # update csv
        write_csv_file(cwd / amort_path, AMORTIZATION_FIELDS, amortizations)
        print("Amortization deleted")

    # def __del__(self):
    #     print("Im am deleted")

    # class method for users registering amortizations

    @classmethod
    def get(cls):
        if len(loans) != 0:
            # Must validate user's input in each step, so that the user does not have to start at the beginning each time his input is invalid
            # id assigned automatically
            if len(amortizations) != 0:
                id = amortizations[-1].id + 1
            else:
                id = 1
            print("Please enter the following data. At any moment press CTRL + D to go back to the previous menu without saving.")
            # input for loan_id
            while True:
                if loan_id := input("Loan id: "):
                    # if loan_id not in loans
                    if not any(str(obj.id) == str(loan_id) for obj in loans):
                        print(
                            f"Invalid input: No loan with id: {loan_id} in database. Please enter one of the following loan ids:")
                        # for obj in loans:
                        #     print(f"Id: {obj.id} Face Value:{obj.face_value} Bank: {obj.bank}")
                        loans_report(loans)
                        continue
                    else:
                        loan_id = int(loan_id)
                        break
            # input for value
            while True:
                if value := input("Amortization value: "):
                    try:
                        value = float(value)
                        if value <= 0:
                            raise ValueError
                    except ValueError:
                        print(
                            "Invalid input: Amortization value must be a positive number")
                        continue
                    else:
                        loan = get_obj(loans, loan_id, "id")
                        loan_principal_balance = loan.principal_balance
                        if value > loan_principal_balance:
                            print(
                                f"Amortization value (${value:,.2f}) can not be greater than loan balance (${loan_principal_balance:,.2f})")
                            continue
                        else:
                            break
            # input for amort_date
            while True:
                if amort_date := input("Amortization date: "):
                    try:
                        amort_date = datetime.strptime(
                            amort_date, '%Y-%m-%d').date()
                    except ValueError:
                        print("Invalid date format, should be YYYY-MM-DD")
                        continue
                    else:
                        loan = get_obj(loans, loan_id, "id")
                        loan_issue_date = loan.issue_date
                        loan_term = loan.loan_term
                        loan_maturity = loan_issue_date + \
                            relativedelta(months=loan_term)
                        today = date.today()
                        if not amort_date <= today:
                            print(
                                f"Amortization date ({str(amort_date)}) can not be greater than today ({str(today)})")
                            continue
                        elif not loan_issue_date < amort_date <= loan_maturity:
                            print(
                                f"Amortization date ({str(amort_date)}) can not be less than or equal to loan issue date ({str(loan_issue_date)}) and can not be greater than loan maturity date ({str(loan_maturity)})")
                            continue
                        else:
                            break
            return cls(id, loan_id, value, amort_date)
        else:
            print("No loans have been created yet. Amortizations can not be registered")


# Loan class
class Loan:
    def __init__(self, id, face_value, bank, issue_date, loan_term, payment_frequency, interest_rate, interest_rate_type,
                 nominal_rate_compounding_period, interest_payment_frequency):
        # Loaded input or user's input
        self.id = id
        self.face_value = face_value
        self.bank = bank
        self.issue_date = issue_date
        self.loan_term = loan_term
        self.payment_frequency = payment_frequency
        self.interest_rate = interest_rate
        self.interest_rate_type = interest_rate_type
        self.nominal_rate_compounding_period = nominal_rate_compounding_period
        self.interest_payment_frequency = interest_payment_frequency

        # additional information
        # at moment of creation or at moment of editing loans. "Loan scheme"
        self.principal_balance = self.face_value
        # Dictionary where keys are dates and values are scheduled amortizations
        self.amort_schedule = {}
        self.scheduled_principals_b_amort = {}
        # Dictionaries where keys are dates and values are principals in each period before and after amortization
        self.scheduled_principals_a_amort = {}
        # Dictionary where keys are dates anda values are scheduled interest payments
        self.interest_payment_schedule = {}

        # amortizations and future cash flow based on actual amortizations
        self.actual_amortizations = []  # List containing amortization objects for this loan
        # Dict containing amortizations for later reports
        self.actual_amortizations_dict = {}
        # Similar to amort_schedule, but takes into account actual amortizations
        self.actual_amort_schedule = self.amort_schedule
        # interest
        # Similar to interest_payment_schedule but takes into account actual amortizations
        self.actual_interest_payment_schedule = self.interest_payment_schedule
        self.actual_principals_b_amort = self.scheduled_principals_b_amort
        self.actual_principals_a_amort = self.scheduled_principals_a_amort

    # Setting properties
    # id: Can only be set the first time the object is constructed

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        if not hasattr(self, 'id'):
            self._id = int(id)
        else:
            raise ValueError("Can't change id manually")

    # face_value: must be an integer or a float
    @property
    def face_value(self):
        return self._face_value

    @face_value.setter
    def face_value(self, face_value):
        try:
            face_value = float(face_value)
            if face_value <= 0:
                raise ValueError
        except ValueError:
            raise ValueError("Face value must be a positive number")
        else:
            # if face_value <= 0:
            #     raise ValueError("Face value must be a positive number")
            self._face_value = face_value

    # bank: must be in the banks database
    @property
    def bank(self):
        return self._bank

    # setter
    @bank.setter
    def bank(self, bank):
        # if bank.lower().title() not in banks:
        if not any(obj.bank == bank.lower().title() for obj in banks):
            raise ValueError(
                "Invalid input: Bank does not exist in the database.")
        # self._bank = bank.lower().title()
        bank = get_obj(banks, bank.lower().title(), "bank")
        self._bank = bank

    # issue_date: must be a valid date
    @property
    def issue_date(self):
        return self._issue_date

    @issue_date.setter
    def issue_date(self, issue_date):
        if not isinstance(issue_date, date):
            try:
                issue_date = datetime.strptime(issue_date, '%Y-%m-%d').date()
            except ValueError:
                print("Invalid date format, should be YYYY-MM-DD")
        self._issue_date = issue_date

    # loan_term: must be a positive integer
    @property
    def loan_term(self):
        return self._loan_term

    @loan_term.setter
    def loan_term(self, loan_term):
        try:
            loan_term = float(loan_term)
            if loan_term % 1 != 0 or loan_term <= 0:
                raise ValueError
        except ValueError:
            # if not type(loan_term) is int or loan_term <= 0:
            raise ValueError(
                "Loan term must be a positive integer. Floating point numbers are not allowed.")
        else:
            self._loan_term = int(loan_term)

    # payment_frequency: loan_term must be divisible by months in frequency period
    @property
    def payment_frequency(self):
        return self._payment_frequency

    @payment_frequency.setter
    def payment_frequency(self, payment_frequency):
        # if frequency not allowed, print an appropriate message
        if not check_frequency(self.loan_term, payment_frequency):
            try:
                period = MONTHS[payment_frequency]
            except KeyError:
                raise ValueError("Invalid payment frequency")
            else:
                raise ValueError(
                    f"Payment frequency and loan term does not match. Loan term ({self.loan_term}) not divisible by months in {payment_frequency} frequency ({period})")
        self._payment_frequency = payment_frequency

    # interest_rate: must be an integer or a float 0<ir<100
    @property
    def interest_rate(self):
        return self._interest_rate

    @interest_rate.setter
    def interest_rate(self, interest_rate):
        try:
            interest_rate = float(interest_rate)
            if interest_rate <= 0 or interest_rate > 100:
                raise ValueError
        except ValueError:
            # if type(interest_rate) not in [int, float] or interest_rate <= 0 or interest_rate > 100:
            raise ValueError(
                "Interest rate must be a positive number between 0 and 100. Floating point numbers are allowed.")
        else:
            self._interest_rate = interest_rate

    # interest_rate_type: must be in the types database
    @property
    def interest_rate_type(self):
        return self._interest_rate_type

    # setter
    @interest_rate_type.setter
    def interest_rate_type(self, interest_rate_type):
        if interest_rate_type.lower() not in TYPES:
            raise ValueError(
                "Invalid input: Rate type does not exist in the database.")
        self._interest_rate_type = interest_rate_type.lower()

    # nominal_rate_compounding_period: must be in database. If rate_type = effective set to annually, else can not set to annually
    @property
    def nominal_rate_compounding_period(self):
        return self._nominal_rate_compounding_period

    # setter
    @nominal_rate_compounding_period.setter
    def nominal_rate_compounding_period(self, nominal_rate_compounding_period):
        if nominal_rate_compounding_period.lower() not in PERIODS:
            raise ValueError(
                "Invalid input: Nominal rate compounding period does not exist in the database.")
        elif self.interest_rate_type == "effective":
            self._nominal_rate_compounding_period = "annually"
        elif self.interest_rate_type == "nominal" and nominal_rate_compounding_period == "annually":
            raise ValueError(
                f"Invalid input: Nominal rate compounding period can not be set to {nominal_rate_compounding_period} because interest rate type was set to nominal rate")
        else:
            self._nominal_rate_compounding_period = nominal_rate_compounding_period.lower()

    # interest_payment_frequency: loan_term must be divisible by months in frequency period
    @property
    def interest_payment_frequency(self):
        return self._interest_payment_frequency

    @interest_payment_frequency.setter
    def interest_payment_frequency(self, interest_payment_frequency):
        if not check_frequency(self.loan_term, interest_payment_frequency):
            try:
                period = MONTHS[interest_payment_frequency]
            except KeyError:
                raise ValueError("Invalid interest payment frequency")
            else:
                raise ValueError(
                    f"Interest payment frequency and loan term does not match. Loan term ({self.loan_term}) not divisible by months in {interest_payment_frequency} frequency ({period})")
        self._interest_payment_frequency = interest_payment_frequency

    # METHODS
    # str method: returns csv-like string
    def __str__(self):
        return f"{self.id},{self.face_value},{self.bank.bank},{str(self.issue_date)},{self.loan_term},{self.payment_frequency},{self.interest_rate},{self.interest_rate_type},{self.nominal_rate_compounding_period},{self.interest_payment_frequency}"

    # add amortization method

    def add_amortization(self, amortization):
        # add amortization an update balance
        self.actual_amortizations.append(amortization)

    # Updating scheduled cash flow

    def update_sch(self):
        self.calculate_amort_schedule()
        self.calculate_principals()
        self.calculate_interest_payment_schedule()

    # Updating future (actual) cash flow based on actual amortizations

    def update_act(self):
        # if len(self.actual_amortizations) != 0:
        self.update_balance()
        self.actual_amort_schedule, self.actual_amortizations_dict = generate_actual_amortization_schedule(
            self.issue_date, self.amort_schedule, self.actual_amortizations, self.principal_balance, self.scheduled_principals_a_amort)
        self.actual_principals_b_amort, self.actual_principals_a_amort = generate_principals(self.face_value,
                                                                                             self.loan_term, self.actual_amort_schedule, self.issue_date)
        self.actual_interest_payment_schedule = generate_interests(self.actual_principals_b_amort, self.interest_rate,
                                                                   self.nominal_rate_compounding_period, self.interest_payment_frequency, self.issue_date)

    def calculate_amort_schedule(self):
        self.amort_schedule = generate_amortizations(
            self.face_value, self.loan_term, self.issue_date, self.payment_frequency)

    def calculate_interest_payment_schedule(self):
        self.interest_payment_schedule = generate_interests(self.scheduled_principals_b_amort, self.interest_rate,
                                                            self.nominal_rate_compounding_period, self.interest_payment_frequency, self.issue_date)

    def calculate_principals(self):
        self.scheduled_principals_b_amort, self.scheduled_principals_a_amort = generate_principals(self.face_value,
                                                                                                   self.loan_term, self.amort_schedule, self.issue_date)

    def update_balance(self):
        self.principal_balance = calculate_principal_balance(
            self.face_value, self.actual_amortizations)

    def edit(self):
        while True:
            # print("Please enter the following data. At any moment press CTRL + D to go back to the previous menu without saving.")
            option = input("Choose an option to edit: (f)ace value, (b)ank, (is)sue date, (l)oan term, (p)ayment frequency, (in)terest rate, interest (r)ate type and nominal rate compounding period, (int)erest payment frequency: ").lower()
            # input for value
            if option == "f":
                # old_value = self.value
                while True:
                    if new_face_value := input("Face value: "):
                        try:
                            new_face_value = float(new_face_value)
                            if new_face_value <= 0:
                                raise ValueError
                        except ValueError:
                            print(
                                "Invalid input: Face value must be a positive number")
                            continue
                        else:
                            if new_face_value < self.face_value - self.principal_balance:
                                print(
                                    f"Face value (${new_face_value:,.2f}) can not be lesser than the sum of loan amortizations (${self.face_value - self.principal_balance:,.2f})")
                                continue
                            else:
                                break
                # Change loan in loans array
                self.face_value = new_face_value
                write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
                self.update_sch()
                self.update_act()
                print("Data saved")
                break
            # input for bank
            elif option == "b":
                # old_date = self.amort_date
                while True:
                    if new_bank := input("Bank: ").lower().title():
                        if not any(obj.bank == new_bank.lower().title() for obj in banks):
                            print(
                                "Invalid input: Bank does not exist in the database. Please enter one of the following banks:")
                            banks_report(banks)
                            continue
                        else:
                            break
                # Change loan in loans array
                self.bank = new_bank
                write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
                print("Data saved")
                break
            # input for issue date
            elif option == "is":
                # old_date = self.amort_date
                while True:
                    if new_issue_date := input("Issue date: "):
                        try:
                            new_issue_date = datetime.strptime(
                                new_issue_date, '%Y-%m-%d').date()
                        except ValueError:
                            print("Invalid date format, should be YYYY-MM-DD")
                            continue
                        else:
                            # checking if there are amortizations in loan
                            if len(self.actual_amortizations) != 0:
                                # checking actual amortization dates
                                min_amort_date = min(
                                    self.actual_amortizations, key=lambda x: x.amort_date).amort_date
                                max_amort_date = max(
                                    self.actual_amortizations, key=lambda x: x.amort_date).amort_date
                                new_maturity_date = new_issue_date + \
                                    relativedelta(months=self.loan_term)
                                if new_issue_date >= min_amort_date:
                                    print(
                                        f"Issue date ({str(new_issue_date)}) can not be greater than or equal to min amortization date ({str(min_amort_date)})")
                                    continue
                                elif new_maturity_date < max_amort_date:
                                    print(
                                        f"Loan maturity ({str(new_maturity_date)}) can not be lesser than max amortization date ({str(max_amort_date)})")
                                    continue
                                else:
                                    break
                            else:
                                break
                # Change loan in loans array
                self.issue_date = new_issue_date
                self.update_sch()
                self.update_act()
                write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
                print("Data saved")
                break
            # input for term
            elif option == "l":
                # old_date = self.amort_date
                while True:
                    if new_loan_term := input("Loan term: "):
                        try:
                            new_loan_term = int(new_loan_term)
                            if new_loan_term <= 0:
                                raise ValueError
                        except ValueError:
                            print(
                                "Invalid input: Loan term must be a positive integer. Floating point numbers are not allowed.")
                            continue
                        else:
                            # checking if there are amortizations in loan
                            if len(self.actual_amortizations) != 0:
                                # checking actual amortization dates
                                max_amort_date = max(
                                    self.actual_amortizations, key=lambda x: x.amort_date).amort_date
                                new_maturity_date = self.issue_date + \
                                    relativedelta(months=new_loan_term)
                                if new_maturity_date < max_amort_date:
                                    print(
                                        f"Loan issue date ({self.issue_date}) plus new loan term ({new_loan_term}) yields a new loan maturity date ({str(new_maturity_date)}) that is lesser than max amortization date ({str(max_amort_date)})")
                                    continue
                            # checking for frequencies: payment
                            if not check_frequency(new_loan_term, self.payment_frequency):
                                period = MONTHS[self.payment_frequency]
                                print(
                                    f"Payment frequency and loan term does not match. Loan term ({new_loan_term}) not divisible by months in {self.payment_frequency} frequency ({period})")
                            elif not check_frequency(new_loan_term, self.interest_payment_frequency):
                                period = MONTHS[self.interest_payment_frequency]
                                print(
                                    f"Interest payment frequency and loan term does not match. Loan term ({new_loan_term}) not divisible by months in {self.interest_payment_frequency} frequency ({period})")
                            else:
                                break
                # Change loan in loans array
                self.loan_term = new_loan_term
                self.update_sch()
                self.update_act()
                write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
                print("Data saved")
                break
            # input for payment frequency
            elif option == "p":
                # old_date = self.amort_date
                while True:
                    if new_payment_frequency := input("Payment frequency: ").lower():
                        if not new_payment_frequency in MONTHS:
                            print(
                                "Invalid input: Payment frequency does not exist in the database. Please enter one of the following payment frequencies:")
                            # for period in MONTHS.keys():
                            #     print(period)
                            # continue
                            print_frequencies()
                        elif not check_frequency(self.loan_term, new_payment_frequency):
                            period = MONTHS[new_payment_frequency]
                            print(
                                f"Payment frequency and loan term does not match. Loan term ({self.loan_term}) not divisible by months in {new_payment_frequency} frequency ({period})")
                        else:
                            break
                # Change loan in loans array
                self.payment_frequency = new_payment_frequency
                self.update_sch()
                self.update_act()
                write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
                print("Data saved")
                break
            # input for interest payment frequency
            elif option == "int":
                # old_date = self.amort_date
                while True:
                    if new_interest_payment_frequency := input("Interest payment frequency: ").lower():
                        if not new_interest_payment_frequency in MONTHS:
                            print(
                                "Invalid input: Interest payment frequency does not exist in the database. Please enter one of the following payment frequencies:")
                            # for period in MONTHS.keys():
                            #     print(period)
                            # continue
                            print_frequencies()
                        elif not check_frequency(self.loan_term, new_interest_payment_frequency):
                            period = MONTHS[new_interest_payment_frequency]
                            print(
                                f"Interest payment frequency and loan term does not match. Loan term ({self.loan_term}) not divisible by months in {new_interest_payment_frequency} frequency ({period})")
                        else:
                            break
                # Change loan in loans array
                self.interest_payment_frequency = new_interest_payment_frequency
                self.update_sch()
                self.update_act()
                write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
                print("Data saved")
                break
            # input for interest rate
            elif option == "in":
                # old_date = self.amort_date
                while True:
                    if new_interest_rate := input("Interest rate (number greater than 0 and less or equal than 100): "):
                        try:
                            new_interest_rate = float(new_interest_rate)
                            if new_interest_rate <= 0 or new_interest_rate > 100:
                                raise ValueError
                        except ValueError:
                            print(
                                "Invalid input: Interest rate must be a positive number less or equal than 100")
                            continue
                        else:
                            break
                # Change loan in loans array
                self.interest_rate = new_interest_rate
                self.update_sch()
                self.update_act()
                write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
                print("Data saved")
                break
           # input for interest rate type and nominal rate compounding period
            elif option == "r":
                # old_date = self.amort_date
                while True:
                    if new_interest_rate_type := input("Interest rate type: ").lower():
                        if new_interest_rate_type not in TYPES:
                            print(
                                "Invalid input: Rate type does not exist in the database. Please enter one of the following rate types:")
                            print_types()
                            continue
                        else:
                            if new_interest_rate_type == "effective":
                                print(
                                    "Nominal rate compounding period will automatically be set to anually, since interest rate type was set to effective rate")
                                new_nominal_rate_compounding_period = "annually"
                            else:
                                while True:
                                    if new_nominal_rate_compounding_period := input("Nominal rate compounding period: ").lower():
                                        if new_nominal_rate_compounding_period not in PERIODS:
                                            print(
                                                "Invalid input: Nominal rate compounding period does not exist in the database. Please enter one of the following:")
                                            # for period in PERIODS.keys():
                                            #     print(period)
                                            print_periods()
                                            continue
                                        elif new_interest_rate_type == "nominal" and new_nominal_rate_compounding_period == "annually":
                                            print(
                                                f"Invalid input: Nominal rate compounding period can not be set to {new_nominal_rate_compounding_period} because interest rate type was set to nominal rate")
                                        else:
                                            break
                            break
                # Change loan in loans array
                self.interest_rate_type = new_interest_rate_type
                self.nominal_rate_compounding_period = new_nominal_rate_compounding_period
                self.update_sch()
                self.update_act()
                write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
                print("Data saved")
                break
            else:
                print("Invalid input. Usage: f for editing face value, b for editing bank, is for issue date, l for loan term,",
                      "p for editing payment frequency, in for editing interest rate, r for editing interest rate type and",
                      "nominal rate compounding period, int for editing interest payment frequency")
                continue

    def delete(self):
        # if loan has amortizations:
        if len(self.actual_amortizations) != 0:
            print(
                "Loan can not be deleted because it has amortizations associated with it")
        else:
            # delete loan from loans list
            loans.remove(self)
            # update csv
            write_csv_file(cwd / loans_path, LOAN_FIELDS, loans)
            print("Loan deleted")

    # def __del__(self):
    #     print("Im am deleted")

    # class method for users registering loans

    @classmethod
    def get(cls):
        if len(banks) != 0:
            # Must validate user's input in each step, so that the user does not have to start at the beginning each time his input is invalid
            # id assigned automatically
            if len(loans) != 0:
                id = loans[-1].id + 1
            else:
                id = 1
            print("Please enter the following data. At any moment press CTRL + D to go back to the previous menu without saving.")
            # input for face_vale
            while True:
                if face_value := input("Face value: "):
                    try:
                        face_value = float(face_value)
                        if face_value <= 0:
                            raise ValueError
                    except ValueError:
                        print("Invalid input: Face value must be a positive number")
                        continue
                    else:
                        break
            # input for bank
            while True:
                if bank := input("Bank: ").lower().title():
                    # if bank not in banks:
                    if not any(obj.bank == bank.lower().title() for obj in banks):
                        print(
                            "Invalid input: Bank does not exist in the database. Please enter one of the following banks:")
                        banks_report(banks)
                        continue
                    else:
                        break
            # input for issue_date
            while True:
                if issue_date := input("Issue date: "):
                    try:
                        issue_date = datetime.strptime(
                            issue_date, '%Y-%m-%d').date()
                    except ValueError:
                        print("Invalid date format, should be YYYY-MM-DD")
                        continue
                    else:
                        break
            # input for loan_term
            while True:
                if loan_term := input("Loan term: "):
                    try:
                        loan_term = int(loan_term)
                        if loan_term <= 0:
                            raise ValueError
                    except ValueError:
                        print(
                            "Invalid input: Loan term must be a positive integer. Floating point numbers are not allowed.")
                        continue
                    else:
                        break
            # input for payment_frequency
            while True:
                if payment_frequency := input("Payment frequency: ").lower():
                    if not payment_frequency in MONTHS:
                        print(
                            "Invalid input: Payment frequency does not exist in the database. Please enter one of the following payment frequencies:")
                        # for period in MONTHS.keys():
                        #     print(period)
                        # continue
                        print_frequencies()
                    elif not check_frequency(loan_term, payment_frequency):
                        period = MONTHS[payment_frequency]
                        print(
                            f"Payment frequency and loan term does not match. Loan term ({loan_term}) not divisible by months in {payment_frequency} frequency ({period})")
                    else:
                        break
            # input for interest_rate
            while True:
                if interest_rate := input("Interest rate (number greater than 0 and less or equal than 100): "):
                    try:
                        interest_rate = float(interest_rate)
                        if interest_rate <= 0 or interest_rate > 100:
                            raise ValueError
                    except ValueError:
                        print(
                            "Invalid input: Interest rate must be a positive number less or equal than 100")
                        continue
                    else:
                        break
            # input for interest_rate_type
            while True:
                if interest_rate_type := input("Interest rate type: ").lower():
                    if interest_rate_type not in TYPES:
                        print(
                            "Invalid input: Rate type does not exist in the database. Please enter one of the following rate types:")
                        print_types()
                        continue
                    else:
                        break
            # input for nominal_rate_compounding_period
            if interest_rate_type == "effective":
                print("Nominal rate compounding period will automatically be set to anually, since interest rate type was set to effective rate")
                nominal_rate_compounding_period = "annually"
            else:
                while True:
                    if nominal_rate_compounding_period := input("Nominal rate compounding period: ").lower():
                        if nominal_rate_compounding_period not in PERIODS:
                            print(
                                "Invalid input: Nominal rate compounding period does not exist in the database. Please enter one of the following:")
                            # for period in PERIODS.keys():
                            #     print(period)
                            print_periods()
                            continue
                        elif interest_rate_type == "nominal" and nominal_rate_compounding_period == "annually":
                            print(
                                f"Invalid input: Nominal rate compounding period can not be set to {nominal_rate_compounding_period} because interest rate type was set to nominal rate")
                        else:
                            break
            # input for interest_payment_frequency
            while True:
                if interest_payment_frequency := input("Interest payment frequency: ").lower():
                    if not interest_payment_frequency in MONTHS:
                        print(
                            "Invalid input: Interest payment frequency does not exist in the database. Please enter one of the following payment frequencies:")
                        # for period in MONTHS.keys():
                        #     print(period)
                        # continue
                        print_frequencies()
                    elif not check_frequency(loan_term, interest_payment_frequency):
                        period = MONTHS[interest_payment_frequency]
                        print(
                            f"Interest payment frequency and loan term does not match. Loan term ({loan_term}) not divisible by months in {interest_payment_frequency} frequency ({period})")
                    else:
                        break
            return cls(id, face_value, bank, issue_date, loan_term, payment_frequency, interest_rate, interest_rate_type, nominal_rate_compounding_period, interest_payment_frequency)
        else:
            print(
                "No banks in database. Please register a bank before registering a loan")


def main():
    # Welcome message with figlet library
    message_to_figlet('Welcome to loMap', 'doom')
    print("-" * 56)
    # Loading data into memory
    # reading banks.csv
    with open(cwd / bank_path) as file:
        reader = csv.DictReader(file)
        for row in reader:
            banks.append(Bank(**row))
    # reading loans.csv
    with open(cwd / loans_path) as file:
        reader = csv.DictReader(file)
        for row in reader:
            loans.append(Loan(**row))
    # reading amortizations.csv
    with open(cwd / amort_path) as file:
        reader = csv.DictReader(file)
        for row in reader:
            # create amortization object, add amortization to amortization lists and add amortization to the loan object
            amortization = Amortization(**row)
            amortizations.append(amortization)
            loan = get_obj(loans, int(row["loan_id"]), "id")
            loan.add_amortization(amortization)
    # Updating loan attributes once all data has ben loaded: for better performance
    for loan in loans:
        loan.update_sch()
        loan.update_act()
    # Main Menu
    menu("main")
    for loan in Loans:
        print(loan)


def menu(op):
    """
    Input: op, an option string that indicates which menu to display
    Renders specified menu
    """
    while True:
        if op == "main":
            message_to_figlet("Main menu", "standard")
            option = input(
                "Choose an option: (m)anage, (r)eports, (q)uit: ").lower()
            match option:
                case "m":
                    menu("manage")
                case "r":
                    menu("reports")
                case "q":
                    message_to_figlet('See you soon!!!', 'standard')
                    sys.exit(0)
                case _:
                    print("Invalid input. Usage: m for managing your loans and amortizations, r for generating reports,",
                          "q for quitting the program")
                    continue
        elif op == "manage":
            message_to_figlet('Management menu', 'standard')
            option = input(
                "Choose an option: (l)oans, (a)mortizations, (b)anks, (g)o back, (q)uit: ").lower()
            match option:
                case "l":
                    menu("loans")
                case "a":
                    menu("amortizations")
                case "b":
                    menu("banks")
                case "g":
                    break
                case "q":
                    message_to_figlet("See you soon", "standard")
                    sys.exit(0)
                case _:
                    print("Invalid input. Usage: l for managing your loans, a for managing your amortizations, b for managing your banks,",
                          "g for going back, q for quitting the program")
                    continue
        elif op == "loans":
            message_to_figlet('Loans menu', 'standard')
            option = input(
                "Choose an option: (c)reate, (e)dit, (d)elete, (g)o back, (q)uit: ").lower()
            match option:
                case "c":
                    try:
                        # get data from user and create a new loan object
                        if loan := Loan.get():
                            # add loan to loan list
                            loans.append(loan)
                            loan.update_sch()
                            loan.update_act()
                            append_csv_file(cwd / loans_path,
                                            LOAN_FIELDS, loan)
                    except EOFError:
                        print()
                        print("Data not saved")
                case "e":
                    while True:
                        if len(loans) != 0:
                            try:
                                if loan_id := input("Please input the loan id you would like to edit (At any moment press CTRL + D to go back to the previous menu): "):
                                    # if loan_id not in loans
                                    if not any(str(obj.id) == str(loan_id) for obj in loans):
                                        print(
                                            f"Invalid input: No loan with id: {loan_id} in database. Please enter one of the following loan ids:")
                                        loans_report(loans)
                                        continue
                                    else:
                                        # get loan based on loan_id
                                        loan = get_obj(
                                            loans, int(loan_id), "id")
                                        loans_report({loan})
                                        loan.edit()
                                        break
                            except EOFError:
                                print()
                                print("Data not saved")
                                break
                        else:
                            print("Loans database is empty")
                            break
                case "d":
                    while True:
                        if len(loans) != 0:
                            try:
                                if loan_id := input("Please input the loan id you would like to delete (At any moment press CTRL + D to go back to the previous menu): "):
                                    # if loan_id not in loans
                                    if not any(str(obj.id) == str(loan_id) for obj in loans):
                                        print(
                                            f"Invalid input: No loan with id: {loan_id} in database. Please enter one of the following loan ids:")
                                        loans_report(loans)
                                        continue
                                    else:
                                        # get loan based on loan_id
                                        loans_report(
                                            {get_obj(loans, int(loan_id), "id")})
                                        get_obj(loans, int(loan_id),
                                                "id").delete()
                                        break
                            except EOFError:
                                print()
                                break
                        else:
                            print("Amortizations database is empty")
                            break
                case "g":
                    break
                case "q":
                    message_to_figlet("See you soon", "standard")
                    sys.exit(0)
                case _:
                    print("Invalid input. Usage: c for creating a new loan, e for editing an existing loan, d for deleting and existing loan,",
                          "g for going back, q for quitting the program")
                    continue
        elif op == "amortizations":
            message_to_figlet('Amortizations menu', 'standard')
            option = input(
                "Choose an option: (c)reate, (e)dit, (d)elete, (g)o back, (q)uit: ").lower()
            match option:
                case "c":
                    try:
                        # get data from user and create a new amortization object
                        if amortization := Amortization.get():
                            # add amortization to amortizations list
                            amortizations.append(amortization)
                            # get loan based on amortization.loan_id and add amortization
                            loan = get_obj(loans, int(
                                amortization.loan_id), "id")
                            loan.add_amortization(amortization)
                            loan.update_act()
                            append_csv_file(cwd / amort_path,
                                            AMORTIZATION_FIELDS, amortization)
                    except EOFError:
                        print()
                        print("Data not saved")
                case "e":
                    while True:
                        if len(amortizations) != 0:
                            try:
                                if amort_id := input("Please input the amortization id you would like to edit (At any moment press CTRL + D to go back to the previous menu): "):
                                    # if amortization_id not in amortizations
                                    if not any(str(obj.id) == str(amort_id) for obj in amortizations):
                                        print(
                                            f"Invalid input: No amortization with id: {amort_id} in database. Please enter one of the following amortization ids:")
                                        amort_report(amortizations)
                                        continue
                                    else:
                                        # get amort based on amortization_id
                                        amortization = get_obj(
                                            amortizations, int(amort_id), "id")
                                        amort_report({amortization})
                                        amortization.edit()
                                        break
                            except EOFError:
                                print()
                                print("Data not saved")
                                break
                        else:
                            print("Amortizations database is empty")
                            break
                case "d":
                    while True:
                        if len(amortizations) != 0:
                            try:
                                if amort_id := input("Please input the amortization id you would like to delete (At any moment press CTRL + D to go back to the previous menu): "):
                                    # if amortization_id not in amortizations
                                    if not any(str(obj.id) == str(amort_id) for obj in amortizations):
                                        print(
                                            f"Invalid input: No amortization with id: {amort_id} in database. Please enter one of the following amortization ids:")
                                        amort_report(amortizations)
                                        continue
                                    else:
                                        # get amort based on amortization_id
                                        amort_report(
                                            {get_obj(amortizations, int(amort_id), "id")})
                                        get_obj(amortizations, int(
                                            amort_id), "id").delete()
                                        break
                            except EOFError:
                                print()
                                break
                        else:
                            print("Amortizations database is empty")
                            break
                case "g":
                    break
                case "q":
                    message_to_figlet("See you soon", "standard")
                    sys.exit(0)
                case _:
                    print("Invalid input. Usage: c for creating a new amortization, e for editing an existing amortization, d for deleting and existing amortization,",
                          "g for going back, q for quitting the program")
                    continue
        elif op == "banks":
            message_to_figlet('Banks menu', 'standard')
            option = input(
                "Choose an option: (c)reate, (e)dit, (d)elete, (g)o back, (q)uit: ").lower()
            match option:
                case "c":
                    try:
                        # get data from user and create a new bank object
                        if bank := Bank.get():
                            # add bank to banks list
                            banks.append(bank)
                            append_csv_file(cwd / bank_path, BANK_FIELDS, bank)
                    except EOFError:
                        print()
                        print("Data not saved")
                case "e":
                    while True:
                        if len(banks) != 0:
                            try:
                                if bank_id := input("Please input the bank id you would like to edit (At any moment press CTRL + D to go back to the previous menu): "):
                                    # if bank_id not in banks
                                    if not any(str(obj.id) == str(bank_id) for obj in banks):
                                        print(
                                            f"Invalid input: No bank with id: {bank_id} in database. Please enter one of the following bank ids:")
                                        banks_report(banks)
                                        continue
                                    else:
                                        # get bank based on bank_id
                                        bank = get_obj(
                                            banks, int(bank_id), "id")
                                        banks_report({bank})
                                        bank.edit()
                                        break
                            except EOFError:
                                print()
                                break
                        else:
                            print("Banks database is empty")
                            break
                case "d":
                    while True:
                        if len(banks) != 0:
                            try:
                                if bank_id := input("Please input the bank id you would like to delete (At any moment press CTRL + D to go back to the previous menu): "):
                                    # if bank_id not in banks
                                    if not any(str(obj.id) == str(bank_id) for obj in banks):
                                        print(
                                            f"Invalid input: No bank with id: {bank_id} in database. Please enter one of the following bank ids:")
                                        banks_report(banks)
                                        continue
                                    else:
                                        # get bank based on bank_id and delete it
                                        banks_report(
                                            {get_obj(banks, int(bank_id), "id")})
                                        get_obj(banks, int(bank_id),
                                                "id").delete()
                                        break
                            except EOFError:
                                print()
                                break
                        else:
                            print("Banks database is empty")
                            break
                case "g":
                    break
                case "q":
                    message_to_figlet("See you soon", "standard")
                    sys.exit(0)
                case _:
                    print("Invalid input. Usage: c for creating a new bank, e for editing an existing bank, d for deleting and existing bank,",
                          "g for going back, q for quitting the program")
                    continue
        elif op == "reports":
            message_to_figlet('Reports menu', 'standard')
            option = input(
                "Choose an option: (l)oans, (a)mortizations, (b)anks, (c)ash flow, (g)o back, (q)uit: ").lower()
            match option:
                case "l":
                    loans_report(loans)
                case "a":
                    amort_report(amortizations)
                case "b":
                    banks_report(banks)
                case "c":
                    while True:
                        if len(loans) != 0:
                            try:
                                if loan_id := input("Please input a loan id for which you would like its cash flow (At any moment press CTRL + D to go back to the previous menu): "):
                                    # if loan_id not in loans
                                    if not any(str(obj.id) == str(loan_id) for obj in loans):
                                        print(
                                            f"Invalid input: No loan with id: {loan_id} in database. Please enter one of the following loan ids:")
                                        if check := loans_report(loans):
                                            break
                                        continue
                                    else:
                                        # get loan based on loan_id
                                        loan = get_obj(
                                            loans, int(loan_id), "id")
                                        loans_report({loan})
                                        cash_flow_report(loan)
                                        break
                            except EOFError:
                                print()
                                break
                        else:
                            print("Loans database is empty")
                            break
                case "g":
                    break
                case "q":
                    message_to_figlet("See you soon", "standard")
                    sys.exit(0)
                case _:
                    print("Invalid input. Usage: l for loans report, a for amortizations report, b for banks report,",
                          "c for cash flow reports, g for going back, q for quitting the program")
                    continue


if __name__ == "__main__":
    main()
