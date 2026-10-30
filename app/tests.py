from datetime import date

from django.test import SimpleTestCase

from .forms import PatientRegisterForm, PatientSelfForm
from .models import Patient


class DateInputFormatTests(SimpleTestCase):
    def test_registration_date_input_uses_day_month_year(self):
        date_field = PatientRegisterForm.base_fields["dob"]
        rendered = str(PatientRegisterForm()["dob"])

        self.assertIn('type="text"', rendered)
        self.assertIn('placeholder="dd/mm/yyyy"', rendered)
        self.assertEqual(date_field.clean("07/03/2001"), date(2001, 3, 7))

    def test_profile_form_parses_day_month_year_date(self):
        form = PatientSelfForm(data={"full_name": "Nguyen Van A", "dob": "07/03/2001"})

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["dob"], date(2001, 3, 7))

    def test_profile_form_displays_date_in_day_month_year(self):
        form = PatientSelfForm(instance=Patient(full_name="Nguyen Van A", dob=date(2001, 3, 7)))

        self.assertIn('value="07/03/2001"', str(form["dob"]))

    def test_profile_form_still_accepts_iso_date(self):
        form = PatientSelfForm(data={"full_name": "Nguyen Van A", "dob": "2001-03-07"})

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["dob"], date(2001, 3, 7))
