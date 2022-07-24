from pathlib import Path
import sys
import os
import unittest
path = str(Path(os.path.abspath(__file__)).parent.parent.parent)
sys.path.insert(1, path)
import api
from tests.integration.test import cases


class TestCharField(unittest.TestCase):
    @cases([
        (42, TypeError, "Value must be str type!"),
        ([42], TypeError, "Value must be str type!"),
        ("", ValueError, "Field is required"),
        (None, ValueError, 'Field is required'),
    ])
    def test_char_field__wrong_type_and_value(self, value, error_type, error_message):
        with self.assertRaises(error_type) as context:
            api.CharField(required=True, nullable=False).validate(value)
        self.assertEqual(error_message, str(context.exception))

    @cases([
        ("42"),
    ])
    def test_char_field__positive(self, value):
        api.CharField(required=True, nullable=False).validate(value)


class TestArgumentField(unittest.TestCase):
    @cases([
        (42, TypeError, "Value must be dict type!"),
        ([42], TypeError, "Value must be dict type!"),
        (None, ValueError, 'Field is required'),
    ])
    def test_argument_field__wrong_type_and_value(self, value, error_type, error_message):
        with self.assertRaises(error_type) as context:
            api.ArgumentsField(required=True, nullable=False).validate(value)
        self.assertEqual(error_message, str(context.exception))

    @cases([
        ({"42": "42"}),
    ])
    def test_argument_field__positive(self, value):
        api.ArgumentsField(required=True, nullable=False).validate(value)


class TestEmailField(unittest.TestCase):
    @cases([
        ("testmail", ValueError, "Email must contain @!"),
        ([42], TypeError, "Value must be str type!"),
        (None, ValueError, 'Field is required'),
    ])
    def test_email_field__wrong_type_and_value(self, value, error_type, error_message):
        with self.assertRaises(error_type) as context:
            api.EmailField(required=True, nullable=False).validate(value)
        self.assertEqual(error_message, str(context.exception))

    @cases([
        ("test@mail.ru"),
    ])
    def test_email_field__positive(self, value):
        api.EmailField(required=True, nullable=False).validate(value)


class TestPhoneField(unittest.TestCase):
    @cases([
        ([1, 2, 3], TypeError, "Value must be str or int type!"),
        ("723456789", ValueError, "Value must be 11 characters!"),
        ("12345678910", ValueError, "Value must start with 7!"),
        (None, ValueError, 'Field is required'),
    ])
    def test_phone_field__wrong_type(self, value, error_type, error_message):
        with self.assertRaises(error_type) as context:
            api.PhoneField(required=True, nullable=False).validate(value)
        self.assertEqual(error_message, str(context.exception))

    @cases([
        ("79998887766"),
    ])
    def test_phone_field__positive(self, value):
        api.PhoneField(required=True, nullable=False).validate(value)


class TestDateField(unittest.TestCase):
    @cases([
        ("111.111.1111", ValueError, "Value must implement pattern XX.XX.XXXX!"),
        ("00.00.0000", ValueError, "Invalid date!"),
        (None, ValueError, 'Field is required'),
    ])
    def test_date_field__wrong_type(self, value, error_type, error_message):
        with self.assertRaises(error_type) as context:
            api.DateField(required=True, nullable=False).validate(value)
        self.assertEqual(error_message, str(context.exception))

    @cases([
        ("28.06.2022"),
    ])
    def test_date_field__positive(self, value):
        api.DateField(required=True, nullable=False).validate(value)


class TestBirthDayField(unittest.TestCase):
    @cases([
        ("111.111.1111", ValueError, "Value must implement pattern XX.XX.XXXX!"),
        ("11.11.1900", ValueError, "Value must be less then 70 years!"),
        ("28.06.2042", ValueError, "Value must be less then current time!"),
        ("00.00.0000", ValueError, "Invalid date!"),
        (None, ValueError, 'Field is required'),
    ])
    def test_birth_day_field__wrong_type(self, value, error_type, error_message):
        with self.assertRaises(error_type) as context:
            api.BirthDayField(required=True, nullable=False).validate(value)
        self.assertEqual(error_message, str(context.exception))

    @cases([
        ("28.06.2022"),
    ])
    def test_birth_day_field__positive(self, value):
        api.BirthDayField(required=True, nullable=False).validate(value)


class TestGenderField(unittest.TestCase):
    @cases([
        ("1", TypeError, "Value must be int type!"),
        (4, ValueError, "Gender must be 0, 1 or 2"),
        (None, ValueError, 'Field is required'),
    ])
    def test_gender_field__wrong_type(self, value, error_type, error_message):
        with self.assertRaises(error_type) as context:
            api.GenderField(required=True, nullable=False).validate(value)
        self.assertEqual(error_message, str(context.exception))

    @cases([
        (1),
    ])
    def test_gender_field__positive(self, value):
        api.GenderField(required=True, nullable=False).validate(value)


class TestCleintIDsField(unittest.TestCase):
    @cases([
        ({"42": "42"}, TypeError, "Value must be list type!"),
        ([1, 2, "3"], ValueError, "Every elements in list must be int type!"),
        (None, ValueError, 'Field is required'),
    ])
    def test_client_ids_field__wrong_type(self, value, error_type, error_message):
        with self.assertRaises(error_type) as context:
            api.ClientIDsField(required=True, nullable=False).validate(value)
        self.assertEqual(error_message, str(context.exception))

    @cases([
        ([1, 2]),
    ])
    def test_client_ids_field__positive(self, value):
        api.ClientIDsField(required=True, nullable=True).validate(value)


if __name__ == "__main__":
    unittest.main()
