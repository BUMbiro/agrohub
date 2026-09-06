from django.test import TestCase
from django.urls import reverse


class PublicPagesTests(TestCase):
    def test_home_page_available(self):
        response = self.client.get(reverse("catalog:home"))
        self.assertEqual(response.status_code, 200)

    def test_contacts_page_available(self):
        response = self.client.get(reverse("catalog:contacts"))
        self.assertEqual(response.status_code, 200)
