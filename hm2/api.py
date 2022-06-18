#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
from multiprocessing.sharedctypes import Value
from tkinter import N
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from dateutil.relativedelta import relativedelta
import re
from scoring import get_interests, get_score

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field(abc.ABC):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

    def validate(self, value):
        if self.required and not value:
            raise ValueError("Field is required")

        if not self.nullable and not value:
            raise ValueError("Field is not nullable")

    @abc.abstractmethod
    def is_empty(self, value):
        raise NotImplemented


class CharField(Field):
    def validate(self, value):
        if self.is_empty(value):
            return

        super().validate(value)
        if not isinstance(value, str):
            raise TypeError("Value must be str type!")

    def is_empty(self, value):
        return not value


class ArgumentsField(Field):
    def validate(self, value):
        super().validate(value)
        if not isinstance(value, dict):
            raise TypeError("Value must be dict type!")

    def is_empty(self, value):
        return not value


class EmailField(CharField):
    def validate(self, value):
        if self.is_empty(value):
            return

        super().validate(value)
        if "@" not in value:
            raise ValueError("Email must contain @!")


class PhoneField(Field):
    def validate(self, value):
        if self.is_empty(value):
            return

        super().validate(value)
        if not isinstance(value, (str, int)):
            raise TypeError("Value must be str or int type!")

        str_value = str(value)

        if len(str_value) != 11:
            raise ValueError("Value must be 11 characters!")

        if not str_value.startswith("7"):
            raise ValueError("Value must start with 7!")

    def is_empty(self, value):
        return not value


class DateField(CharField):
    def _parse_date(self, value):
        return datetime.datetime.strptime(value, "%d.%m.%Y")

    def validate(self, value):
        if self.is_empty(value):
            return

        super().validate(value)

        if not re.match(r"^\d{2}\.\d{2}.\d{4}$", value):
            raise ValueError("Value must implement pattern XX.XX.XXXX!")

        try:
            self._parse_date(value)
        except Exception:
            raise ValueError("Invalid date!")


class BirthDayField(DateField):
    def validate(self, value):
        if self.is_empty(value):
            return

        super().validate(value)

        if self._parse_date(value) + relativedelta(years=70) < datetime.datetime.now():
            raise ValueError("Value must be less then 70 years!")

        if self._parse_date(value) > datetime.datetime.now():
            raise ValueError("Value must be less then current time!")

    def is_empty(self, value):
        return not value


class GenderField(Field):
    def validate(self, value):
        if self.is_empty(value):
            return

        super().validate(value)
        if not isinstance(value, int):
            raise TypeError("Value must be int type!")

        if value not in [0, 1, 2]:
            raise ValueError("Gender must be 0, 1 or 2")

    def is_empty(self, value):
        return not value


class ClientIDsField(Field):
    def validate(self, value):
        super().validate(value)
        if not isinstance(value, list):
            raise TypeError("Value must be list type!")

        if self.is_empty(value):
            return

        for element in value:
            if not isinstance(element, int):
                raise ValueError("Every elements in list must be int type!")

    def is_empty(self, value):
        return not value


class AbstractRequest(abc.ABC):
    def __init__(self, **kwargs):
        self.errors = {}
        self.fields = {}

        for field_name in dir(self):
            field_value = getattr(self, field_name, None)
            if isinstance(field_value, Field):
                self.fields[field_name] = field_value
                setattr(self, field_name, kwargs.get(field_name, None))

    def validate(self):
        for field in self.fields:
            try:
                self.fields[field].validate(getattr(self, field, None))
            except (TypeError, ValueError) as e:
                self.errors[field] = str(e)


class ClientsInterestsRequest(AbstractRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def return_answer(self, store, context, is_admin):
        context["nclients"] = len(self.client_ids)
        return {str(cid):  get_interests(store=store, cid=cid) for cid in self.client_ids}


class OnlineScoreRequest(AbstractRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(self, **kwargs):
        self.field_pairs = [
            ("phone", "email"),
            ("first_name", "last_name"),
            ("gender", "birthday")
        ]
        super().__init__(**kwargs)

    def validate(self):
        super().validate()

        is_vailed_pair = False
        for pair in self.field_pairs:
            is_vailed_first_arg = False
            is_vailed_second_arg = False
            value_arg_1 = "gender" if isinstance(self.fields[pair[0]], GenderField) and getattr(
                self, pair[0], None) != None else getattr(self, pair[0], None)  # fix gender value = 0 problem
            if value_arg_1 or not self.fields[pair[0]].is_empty(value_arg_1):
                is_vailed_first_arg = True

            value_arg_2 = getattr(self, pair[1], None)
            if value_arg_2 or not self.fields[pair[1]].is_empty(value_arg_2):
                is_vailed_second_arg = True

            if is_vailed_first_arg and is_vailed_second_arg:
                is_vailed_pair = True

        if not is_vailed_pair:
            self.errors['Invalid pair'] = "Request doesn't have valid pair"

    def return_answer(self, store, context, is_admin):
        filled_field_names = [
            field_name
            for field_name in self.fields.keys()
            # fix gender value = 0 problem
            if getattr(self, field_name, None) or getattr(self, field_name, None) == 0
        ]
        context["has"] = filled_field_names

        if is_admin:
            result = 42
        else:
            result = get_score(
                store=store,
                phone=self.phone, email=self.email,
                birthday=self.birthday, gender=self.gender,
                first_name=self.first_name, last_name=self.last_name
            )

        return {"score": result}


class MethodRequest(AbstractRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime(
            "%Y%m%d%H") + ADMIN_SALT).encode()).hexdigest()
    else:
        digest = hashlib.sha512(
            (f"{request.account}{request.login}{SALT}").encode()).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    handlers = {
        "online_score": OnlineScoreRequest,
        "clients_interests": ClientsInterestsRequest
    }

    methodrequest = MethodRequest(**request["body"])
    if methodrequest.errors:
        return methodrequest.errors, INVALID_REQUEST

    if not methodrequest.arguments:
        return ERRORS[INVALID_REQUEST], INVALID_REQUEST

    if methodrequest.method not in handlers:
        msg = f"Unrecognize method {methodrequest.method}"
        return msg, NOT_FOUND

    if not check_auth(methodrequest):
        return ERRORS[FORBIDDEN], FORBIDDEN

    handler = handlers[methodrequest.method](**methodrequest.arguments)
    handler.validate()

    if handler.errors:
        return handler.errors, INVALID_REQUEST

    return handler.return_answer(store, ctx, methodrequest.is_admin), OK


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" %
                         (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(
                code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode())
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=80)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
