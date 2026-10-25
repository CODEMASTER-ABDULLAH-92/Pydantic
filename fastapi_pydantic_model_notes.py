"""
FASTAPI + PYDANTIC — FORMATTED LEARNING NOTES
=============================================

Purpose
-------
This file explains the Pydantic concepts used when defining data models for a
FastAPI application. It is written as study notes with small, runnable examples.

Install
-------
    python -m pip install "pydantic[email]"

If you are using FastAPI as well:
    python -m pip install fastapi uvicorn "pydantic[email]"

Important distinction
---------------------
- Pydantic is a Python library for parsing and validating data.
- A Pydantic model describes the shape and rules of data.
- FastAPI uses Pydantic models to validate request bodies and document API
  schemas automatically.
- A Pydantic model is NOT the same thing as a database model. For example,
  SQLAlchemy models commonly describe database tables; Pydantic models
  commonly describe and validate data entering or leaving an API.

Why do we use Pydantic?
-----------------------
Imagine an API receives this dictionary from a client:

    {"name": "Abdullah", "age": "30", "email": "not-an-email"}

Without validation, your application might have to check every field manually.
Pydantic can:
1. Check that required fields are present.
2. Check data types and constraints.
3. Parse compatible input values when non-strict validation is enabled.
4. Produce useful validation errors when data is invalid.
5. Validate one field using a custom rule.
6. Validate relationships between multiple fields.
7. Create derived/computed fields.
8. Represent nested objects.
9. Serialize model data into dictionaries or JSON.

Pydantic validates data; it does not automatically save it to a database.

Version note
------------
This file uses Pydantic v2 syntax: field_validator, model_validator,
computed_field, model_dump, and model_dump_json.
"""

from typing import Annotated, Optional

from pydantic import (
    AnyUrl,
    BaseModel,
    EmailStr,
    Field,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)


# =============================================================================
# 1. THE BASIC PYDANTIC MODEL
# =============================================================================

class BasicPatient(BaseModel):
    """
    BaseModel is the parent class that gives this class Pydantic behaviour.

    Each class attribute becomes a field:
    - name: str means name should be a string.
    - age: int means age should be an integer (or a compatible input value
      that Pydantic can parse, unless strict validation is requested).
    """

    name: str
    age: int
    email: str


# Example:
basic_patient = BasicPatient(
    name="Abdullah",
    age="30",  # Pydantic normally parses this compatible string as integer 30.
    email="abdullah@example.com",
)

print("BASIC MODEL")
print(basic_patient)
print(basic_patient.name)
print(basic_patient.age)
print()


# =============================================================================
# 2. FIELD TYPES AND FIELD CONSTRAINTS
# =============================================================================

class PatientFields(BaseModel):
    """
    Field types and Field(...) constraints describe what data is acceptable.

    Field constraints used here:
    - max_length=50: string must be no longer than 50 characters.
    - gt=0: age must be greater than 0.
    - lt=120: age must be less than 120.
    - max_length=5 on allergies: list may contain at most 5 items.
    - strict=True on weight: do not coerce a string such as "63.2" to float.
    """
    
    # Annotated allows you to add extra information or rules to a type without changing the original type itself.
    name: Annotated[
        str,
        Field(
            max_length=50,
            title="Name of the patient",
            description="Enter the patient's name in at most 50 characters.",
            examples=["Abdullah", "Rajab"],
        ),
    ]

    age: int = Field(gt=0, lt=120)

    # EmailStr validates email-like syntax. Install the optional dependency with:
    # python -m pip install "pydantic[email]"
    email: EmailStr

    # AnyUrl validates that the value is a URL.
    linkedin_url: AnyUrl

    # Default value is used if weight is omitted.
    # strict=True prevents type coercion for this field.
    weight: Annotated[
        float,
        Field(
            default=45.5,
            strict=True,
            description="Weight of the patient in kilograms.",
        ),
    ]

    # Optional[List[str]] means the value can be a list of strings or None.
    # It does NOT by itself make the field optional to omit in Pydantic v2.
    # Giving it a default of None allows the field to be omitted.
    allergies: Annotated[
        Optional[list[str]],
        Field(max_length=5, description="Up to five allergies."),
    ] = None

    # Dict[str, str] means both keys and values should be strings.
    contact_details: dict[str, str]


# Example valid input:
patient_fields = PatientFields(
    name="Abdullah",
    age=30,
    email="abdullah@example.com",
    linkedin_url="https://www.linkedin.com/in/abdullah",
    # weight omitted -> default 45.5 is used
    allergies=["pollen", "dust"],
    contact_details={"email": "abdullah@example.com", "phone": "03001234567"},
)

print("FIELD CONSTRAINTS")
print(patient_fields)
print("Default weight:", patient_fields.weight)
print()


# =============================================================================
# 3. STRICT VALIDATION VS TYPE COERCION
# =============================================================================

"""
By default, Pydantic attempts to parse compatible values.
For example, age="30" can be parsed as age=30.

Strict validation disables that conversion for a strict field.
For example, weight="63.2" is rejected when weight is strict=True because the
input is a string, not a Python float.

Strictness is useful when you want to reject values that are not already of the
expected type. Whether to use it depends on the API's requirements.
"""

try:
    PatientFields(
        name="Abdullah",
        age=30,
        email="abdullah@example.com",
        linkedin_url="https://www.linkedin.com/in/abdullah",
        weight="63.2",  # Invalid: strict float expects a Python float here.
        contact_details={},
    )
except ValidationError as error:
    print("STRICT VALIDATION EXAMPLE")
    print(error)
    print()


# =============================================================================
# 4. CUSTOM FIELD VALIDATORS
# =============================================================================

class PatientWithFieldValidators(BaseModel):
    """
    @field_validator runs custom validation for a particular field.

    This example:
    1. Checks the email domain against an allowed list.
    2. Converts the name to uppercase.

    Note: the domain allow-list is a teaching example. Real systems should use
    the exact domain policy required by the application.
    """

    name: str
    age: int
    email: EmailStr
    weight: float
    allergies: list[str] = Field(default_factory=list)
    contact_details: dict[str, str] = Field(default_factory=dict)

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, value: EmailStr) -> EmailStr:
        allowed_domains = {"hbl.com", "mcb.com", "ubl.com"}
        domain_name = str(value).rsplit("@", 1)[-1].lower()

        if domain_name not in allowed_domains:
            raise ValueError(
                "Email domain must be one of: hbl.com, mcb.com, or ubl.com."
            )

        return value

    @field_validator("name")
    @classmethod
    def transform_name(cls, value: str) -> str:
        # Return the transformed value so the stored field is uppercase.
        return value.strip().upper()


patient_validated = PatientWithFieldValidators(
    name="abdullah",
    age=30,
    email="abdullah@hbl.com",
    weight=63.2,
    allergies=["pollen", "dust"],
    contact_details={"phone": "03001234567"},
)

print("FIELD VALIDATORS")
print("Transformed name:", patient_validated.name)  # ABDULLAH
print("Validated email:", patient_validated.email)
print()


# =============================================================================
# 5. MODEL VALIDATORS — CHECKING MULTIPLE FIELDS TOGETHER
# =============================================================================

class PatientWithModelValidator(BaseModel):
    """
    @model_validator(mode="after") runs after the model's fields have been
    validated and the model instance has been created.

    Use it when a rule depends on multiple fields.

    Rule in this example:
    A patient older than 60 must have an "emergency" entry in contact_details.
    """

    name: str
    age: int
    email: EmailStr
    weight: float
    allergies: list[str] = Field(default_factory=list)
    contact_details: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_emergency_contact(self):
        if self.age > 60 and "emergency" not in self.contact_details:
            raise ValueError(
                "Patients older than 60 must have an emergency contact."
            )
        return self


patient_with_emergency = PatientWithModelValidator(
    name="Abdullah",
    age=65,
    email="abdullah@example.com",
    weight=63.2,
    contact_details={
        "emergency": "03001234567",
        "email": "abdullah@example.com",
    },
)

print("MODEL VALIDATOR")
print("Patient passed the emergency-contact rule:", patient_with_emergency.name)
print()


# =============================================================================
# 6. COMPUTED FIELDS
# =============================================================================

class PatientWithBMI(BaseModel):
    """
    @computed_field includes a derived value when the model is serialized.

    BMI formula:
        BMI = weight in kilograms / (height in metres ** 2)

    BMI is calculated from weight and height; the caller does not supply BMI.

    Important:
    - height must be defined because the calculation uses it.
    - computed_field does not replace validation of weight and height.
    - This is a computed property, not a database column by itself.
    """

    name: str
    age: int = Field(gt=0, lt=120)
    weight: float = Field(gt=0, description="Weight in kilograms.")
    height: float = Field(gt=0, description="Height in metres.")

    @computed_field
    @property
    def calculate_bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)


def insert_patient_info(patient: PatientWithBMI) -> None:
    """
    The type annotation says this function expects a PatientWithBMI instance.
    It does not insert data into a database despite the function's name.
    To store data, you would need database code.
    """
    print("Name:", patient.name)
    print("Age:", patient.age)
    print("BMI:", patient.calculate_bmi)


patient_bmi = PatientWithBMI(
    name="Abdullah",
    age=30,
    weight=63.2,
    height=1.72,
)

print("COMPUTED FIELD")
insert_patient_info(patient_bmi)
print()


# =============================================================================
# 7. NESTED PYDANTIC MODELS
# =============================================================================

class Address(BaseModel):
    """A separate model for address-related data."""

    city: str
    state: str
    pin: str


class PatientWithAddress(BaseModel):
    """
    address: Address means the address field must match the Address model.

    Pydantic can accept either:
    - an Address instance, or
    - a compatible dictionary, which it validates and converts into Address.
    """

    name: str
    gender: str
    age: int
    address: Address


address_data = {
    "city": "Kharian",
    "state": "Punjab",
    "pin": "373777",
}

# Correct: create an Address instance by calling Address, not the dictionary.
address = Address(**address_data)

patient_data = {
    "name": "Abdullah",
    "gender": "male",
    "age": 23,
    "address": address,
}

patient_nested = PatientWithAddress(**patient_data)

# You can also pass address_data directly:
patient_nested_from_dict = PatientWithAddress(
    name="Abdullah",
    gender="male",
    age=23,
    address=address_data,
)

print("NESTED MODEL")
print(patient_nested)
print("City:", patient_nested.address.city)
print()


# =============================================================================
# 8. SERIALIZATION — CONVERTING A MODEL TO A DICTIONARY OR JSON
# =============================================================================

"""
Serialization means converting a model into a representation that can be sent
or stored, such as a dictionary or JSON string.

model_dump()
    Returns a Python dictionary.

model_dump(include=[...])
    Keeps only the selected fields.

model_dump(exclude=[...])
    Removes selected fields.

model_dump_json()
    Returns a JSON string.

Nested Pydantic models are serialized recursively.
"""

print("SERIALIZATION")

# Include only name and gender:
print(patient_nested.model_dump(include={"name", "gender"}))

# Exclude name and gender:
print(patient_nested.model_dump(exclude={"name", "gender"}))

# Serialize the complete model, including nested address:
print(patient_nested.model_dump())

# Convert the model to a JSON string:
print(patient_nested.model_dump_json())
print()


# =============================================================================
# 9. HOW FASTAPI USES A PYDANTIC MODEL
# =============================================================================

"""
This small example shows where a Pydantic model fits into a FastAPI endpoint.

Install FastAPI and Uvicorn if needed:
    python -m pip install fastapi uvicorn "pydantic[email]"

Save this file, or copy this section into a file such as main.py. Then run:
    uvicorn main:app --reload

The `app = FastAPI()` object and the endpoint below are kept in a separate
function so this learning-notes file can run its examples without requiring
FastAPI to be installed. Uncomment the example and add the import if you want
to run the API.

Example endpoint:

    from fastapi import FastAPI
    from pydantic import BaseModel, Field

    app = FastAPI()

    class PatientCreate(BaseModel):
        name: str = Field(min_length=1, max_length=50)
        age: int = Field(gt=0, lt=120)

    @app.post("/patients")
    def create_patient(patient: PatientCreate):
        return {
            "message": "Patient data validated successfully",
            "patient": patient.model_dump(),
        }

What happens when a client sends a request?
1. FastAPI reads the JSON request body.
2. It asks Pydantic to validate the body against PatientCreate.
3. If the data is valid, the endpoint receives a PatientCreate instance.
4. If the data is invalid, FastAPI returns a validation error response (normally
   HTTP 422) without running the endpoint function.
5. FastAPI also uses model information to generate API documentation/OpenAPI.
"""


# =============================================================================
# 10. IMPORTANT FIXES TO REMEMBER FROM THE ORIGINAL CLASSROOM EXAMPLE
# =============================================================================

"""
1. Do not define several unrelated classes with the exact same name `Patient`
   in one file unless you intentionally want to replace the earlier class.
   Each later `class Patient(BaseModel)` rebinds the name Patient, so the
   earlier class is no longer accessible by that name. Use clear names such as
   PatientFields, PatientWithFieldValidators, and PatientWithBMI in notes.

2. The original BMI property used self.height, but height was not declared.
   Add height to the model before calculating BMI.

3. The original sample patient dictionary omitted required fields such as email
   and linkedin_url from the first Patient model. Every required field must be
   supplied unless it has a default.

4. `Optional[list[str]]` means a value may be a list or None. In Pydantic v2,
   to allow the caller to omit the field, give it a default, for example:
       allergies: Optional[list[str]] = None

5. To create a nested model, call the class:
       address = Address(**address_data)
   Do not call the dictionary as if it were a class:
       address_data(**address_data)  # incorrect

6. `insert_patient_info()` only prints values. Its name does not make it a
   database insert function. A real database insert needs database/session code.

7. `EmailStr` and `AnyUrl` perform built-in validation. A custom
   `@field_validator` is useful when your application needs an additional rule,
   such as restricting email addresses to an allow-list of domains.

8. A Pydantic model validates and shapes data. It is not, by itself, a database
   table, authentication system, or persistence layer.
"""


# =============================================================================
# 11. QUICK REVISION
# =============================================================================

"""
BaseModel
    Creates a Pydantic model with parsing and validation.

Field(...)
    Adds constraints and metadata such as gt, lt, max_length, title, and
    description.

Annotated[Type, Field(...)]
    Combines a Python type with extra validation rules/metadata.

EmailStr
    Validates email-like syntax. Requires `python -m pip install "pydantic[email]"`.

AnyUrl
    Validates URL values.

strict=True
    Rejects coercion for the relevant field.

Optional[T]
    Allows None as a value. In Pydantic v2, it does not automatically mean
    the field may be omitted; use a default such as `= None`.

@field_validator("field_name")
    Adds custom validation/transformation for one field.

@model_validator(mode="after")
    Adds a rule involving the fully validated model and multiple fields.

@computed_field
    Includes a derived property in serialization.

Nested model
    Uses another BaseModel as a field type to structure related data.

model_dump()
    Returns a Python dictionary.

model_dump_json()
    Returns a JSON string.

FastAPI request-body model
    FastAPI uses the Pydantic model to validate incoming JSON before calling
    the endpoint.
"""


if __name__ == "__main__":
    print("All learning-note examples completed.")
