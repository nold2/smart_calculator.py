from collections import deque

from .commands import Command, CommandCenter
from .digits import Digit
from .exceptions import CustomError
from .memories import Memory
from .operators import Operator
from .variables import Variable


class Calculator:
    """A Calculator for parsed mathematical equation based on operand and operator"""

    def __init__(self, buffer, memory):
        self.buffer = buffer
        self.memory = memory
        self.__commands = None
        self.__result = deque()
        self.__operators = deque()
        self.precedence_table = {
            "^": 2,
            "*": 1,
            "/": 1,
            "+": 0,
            "-": 0,
            "(": -1,
            ")": 1,
        }

    def calculate(self):
        for v in self.buffer:
            if isinstance(v, Digit):
                self.__result.append(v)
            else:
                pass
            # try:
            #     self.__result.append(int(v))
            # except ValueError:
            #     try:
            #         if v == "(":
            #             self.__operators.append(v)
            #         elif v == ")":
            #             operator = self.__operators.pop()
            #             while not operator == "(":
            #                 second_operand = self.__result.pop()
            #                 first_operand = self.__result.pop()
            #                 result = getattr(Operator(operator), Operator(operator).operator)(first_operand,
            #                                                                                   second_operand)
            #
            #                 self.__result.append(result)
            #                 operator = self.__operators.pop()
            #         elif Variable.is_valid(v):
            #             self.__result.append(int(self.memory.get(v)))
            #         else:
            #             while len(self.__operators) and self.precedence_table.get(v) <= self.precedence_table.get(
            #                     self.__operators[-1]):
            #                 operator = self.__operators.pop()
            #                 second_operand = self.__result.pop()
            #                 first_operand = self.__result.pop()
            #                 result = getattr(Operator(operator), Operator(operator).operator)(first_operand,
            #                                                                                   second_operand)
            #
            #                 self.__result.append(result)
            #             self.__operators.append(v)
            #
            #     except TypeError:
            #         print("What the fuck!", v)

        while len(self.__operators):
            operator = self.__operators.pop()
            second_operand = self.__result.pop()
            first_operand = self.__result.pop()
            self.__result.append(
                getattr(Operator(operator), Operator(operator).operator)(first_operand, second_operand))

        return self.__result.pop()


class Tokenizer:
    def __init__(self, buffer, operators=None):
        if operators is None:
            operators = Operator.OPERATOR

        self.buffer = buffer
        self.pos = 0
        self.operators = operators
        self.tokens = deque()

    def __next_token(self):
        atom = self.__get_atom()
        while atom and atom.isspace():
            self.pos += 1
            atom = self.__get_atom()

        if atom is None:
            return None
        if Digit.is_check(atom):
            return self.__tokenize(Digit)
        if Operator.is_check(atom):
            return self.__tokenize(Operator)

    def __tokenize(self, meta):
        end_pos = self.pos + 1
        while self.__get_atom(end_pos) and meta.is_check(self.__get_atom(end_pos)):
            end_pos += 1

        value = self.buffer[self.pos:end_pos]
        self.pos = end_pos

        return meta(value)

    def __get_atom(self, pos=None):
        current_pos = pos or self.pos

        try:
            return self.buffer[current_pos]
        except IndexError:
            return None

    def tokenize(self):
        while True:
            token = self.__next_token()

            if not token:
                break
            else:
                self.tokens.append(token)

        return self.tokens


class Validator:
    """Validates user input before any actions occur"""

    def __init__(self, content, memory):
        self.content = content
        self.memory = memory

    def validate(self):
        if not self.content:
            return self.format(error=CustomError(message=None))

        if self.content.startswith("/"):
            return self.format(success=Command(instruction=self.content.split("/")[1]))

        if self.is_assignment(content=self.content):
            key = self.extract_key(self.content)
            value = self.extract_value(self.content)

            if not Variable.is_valid(key):
                return self.format(error=CustomError(message="Invalid identifier"))

            if not Validator.is_valid_assignee(value):
                return self.format(error=CustomError(message="Invalid assignment"))

            if not self.is_in_memory(value):
                return self.format(error=CustomError(message="Unknown variable"))

            return self.format(success=({key: value}))

        if Variable.is_valid(variable=self.content) and not self.is_in_memory(content=self.content):
            return self.format(error=CustomError(message="Unknown variable"))

        if len(self.content.split()) == 1 and not self.is_valid_assignee(content=self.content):
            return self.format(error=CustomError(message="Unknown variable"))

        else:
            return self.format(success=Tokenizer(buffer=self.content))

    @staticmethod
    def format(success=None, error=None):
        return success, error

    def is_in_memory(self, content):
        try:
            return type(int(content)) == int
        except ValueError:
            return type(self.memory.get(content)) == int

    @staticmethod
    def is_valid_assignee(content):
        try:
            return Variable.is_valid(variable=content) or type(int(content)) == int
        except (TypeError, ValueError):
            return False

    @staticmethod
    def is_assignment(content):
        return content.count("=")

    @staticmethod
    def extract_key(contents):
        key, *_ = [x.strip() for x in contents.split("=") if x.strip()]
        return key

    @staticmethod
    def extract_value(contents):
        try:
            _, value = [x.strip() for x in contents.split("=") if x.strip()]
            return value
        except ValueError:
            return None


def main():
    memory = Memory()
    while True:
        user_input = input()

        success, error = Validator(user_input, memory).validate()

        if isinstance(error, CustomError):
            error.display()
            continue

        if isinstance(success, Command):
            command_center = CommandCenter(command=success)
            command_center.execute()

        if isinstance(success, dict):
            memory.update(success)

        if isinstance(success, Tokenizer):
            parsed_tokens = success.tokenize()
            print(parsed_tokens)

            calculator = Calculator(buffer=parsed_tokens, memory=memory)
            calculator.calculate()
            # calculator.print()


main()