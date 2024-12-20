######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
TestInventory API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from unittest.mock import patch, MagicMock
from wsgi import app
from service.common import status
from service.models import db, Inventory, DataValidationError
from .factories import InventoryFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)

BASE_URL = "/api/inventories"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Inventory).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Inventory REST API Service", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Healthy")

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_inventory(self):
        """It should Create a new Inventory"""
        test_inventory = InventoryFactory()
        logging.debug("Test Inventory: %s", test_inventory.serialize())
        response = self.client.post(BASE_URL, json=test_inventory.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_inventory = response.get_json()
        self.assertEqual(new_inventory["name"], test_inventory.name)
        self.assertEqual(new_inventory["quantity"], test_inventory.quantity)
        self.assertEqual(new_inventory["restock_level"], test_inventory.restock_level)
        self.assertEqual(new_inventory["condition"], test_inventory.condition.name)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_inventory = response.get_json()
        self.assertEqual(new_inventory["name"], test_inventory.name)
        self.assertEqual(new_inventory["quantity"], test_inventory.quantity)
        self.assertEqual(new_inventory["restock_level"], test_inventory.restock_level)
        self.assertEqual(new_inventory["condition"], test_inventory.condition.name)

    def test_get_inventory(self):
        """It should Get a single Inventory"""
        # get the id of a inventory
        test_inventory = self._create_inventories(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_inventory.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_inventory.name)

    def test_get_inventory_not_found(self):
        """It should not Get a Inventory thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    # ----------------------------------------------------------
    # TEST LIST
    # ----------------------------------------------------------
    def test_get_inventory_list(self):
        """It should Get a list of inventories"""
        self._create_inventories(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    # ----------------------------------------------------------
    # TEST QUERY
    # ----------------------------------------------------------
    def test_query_by_name(self):
        """It should Query Inventory by name"""
        inventories = self._create_inventories(5)
        test_name = inventories[0].name
        name_count = len(
            [inventory for inventory in inventories if inventory.name == test_name]
        )
        response = self.client.get(BASE_URL, query_string=f"name={test_name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), name_count)
        # check the data just to be sure
        for inventory in data:
            self.assertEqual(inventory["name"], test_name)

    def test_query_by_quantity(self):
        """It should Query Inventories by Category"""
        inventories = self._create_inventories(10)
        test_quantity = inventories[0].quantity
        quantity_inventories = [
            inventory
            for inventory in inventories
            if inventory.quantity == test_quantity
        ]
        response = self.client.get(BASE_URL, query_string=f"quantity={test_quantity}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), len(quantity_inventories))
        # check the data just to be sure
        for inventory in data:
            self.assertEqual(inventory["quantity"], test_quantity)

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------
    def test_update_inventory(self):
        """It should Update an existing Inventory"""
        # create a inventory to update
        test_inventory = InventoryFactory()
        response = self.client.post(BASE_URL, json=test_inventory.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the inventory
        new_inventory = response.get_json()
        logging.debug(new_inventory)
        new_inventory["quantity"] = new_inventory["quantity"] + 100
        temp = new_inventory["quantity"]
        response = self.client.put(
            f"{BASE_URL}/{new_inventory['id']}", json=new_inventory
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_inventory = response.get_json()
        self.assertEqual(updated_inventory["quantity"], temp)

    # ----------------------------------------------------------
    # TEST QUERY
    # ----------------------------------------------------------
    def test_query_by_restock_level(self):
        """It should Query Inventory by Restock level"""
        inventories = self._create_inventories(10)
        test_restock_level = inventories[0].restock_level
        restock_level_inventories = [
            inventory
            for inventory in inventories
            if inventory.restock_level == test_restock_level
        ]
        response = self.client.get(
            BASE_URL, query_string=f"restock_level={test_restock_level}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), len(restock_level_inventories))
        # check the data just to be sure
        for inventory in data:
            self.assertEqual(inventory["restock_level"], test_restock_level)

    def test_query_by_condition(self):
        """It should Query Inventory by Condition"""
        inventories = self._create_inventories(10)
        test_condition = inventories[0].condition
        condition_inventories = [
            inventory
            for inventory in inventories
            if inventory.condition == test_condition
        ]
        response = self.client.get(
            BASE_URL, query_string=f"condition={test_condition.name}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), len(condition_inventories))
        # check the data just to be sure
        for inventory in data:
            self.assertEqual(inventory["condition"], test_condition.name)

    def test_query_by_restocking_available(self):
        """It should Query Inventory by Restocking Available"""
        inventories = self._create_inventories(10)
        test_restocking_available = inventories[0].restocking_available
        restocking_available_inventories = [
            inventory
            for inventory in inventories
            if inventory.restocking_available == test_restocking_available
        ]
        response = self.client.get(
            BASE_URL, query_string=f"restocking_available={test_restocking_available}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), len(restocking_available_inventories))
        # check the data just to be sure
        for inventory in data:
            self.assertEqual(
                inventory["restocking_available"], test_restocking_available
            )

    def test_update_non_existing_inventory(self):
        """It test how the system handle a bad update request"""
        test_inventory = InventoryFactory()
        response = self.client.put(f"{BASE_URL}/2000", json=test_inventory.serialize())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_wrong_media(self):
        """It test how the system handle wrong media type request"""
        test_inventory = InventoryFactory()
        response = self.client.post(
            BASE_URL, data=test_inventory.serialize()
        )  # send as form type
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_no_content_type(self):
        """It test how the system handle a request without content_type"""
        response = self.client.post(BASE_URL, headers={})
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------
    def test_delete_inventory(self):
        """It should Delete an Inventory"""
        # Create a test inventory
        test_inventory = self._create_inventories(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_inventory.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete the inventory
        response = self.client.delete(f"{BASE_URL}/{test_inventory.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Ensure it was deleted
        response = self.client.get(f"{BASE_URL}/{test_inventory.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existing_inventory(self):
        """It should return 204 when trying to delete a non-existing Inventory"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ----------------------------------------------------------
    # TEST ACTIONS
    # ----------------------------------------------------------
    def test_start_restock_an_inventory(self):
        """It should start restock for an inventory"""
        inventories = self._create_inventories(10)
        available_inventories = [
            inventory
            for inventory in inventories
            if inventory.restocking_available is True
        ]
        inventory = available_inventories[0]
        response = self.client.put(f"{BASE_URL}/{inventory.id}/start_restock")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(f"{BASE_URL}/{inventory.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        logging.debug("Response data: %s", data)
        self.assertEqual(data["restocking_available"], False)

    def test_start_restock_not_available(self):
        """It should not start restock a Inventory that is not available"""
        inventories = self._create_inventories(10)
        unavailable_inventories = [
            inventory
            for inventory in inventories
            if inventory.restocking_available is False
        ]
        if unavailable_inventories:
            inventory = unavailable_inventories[0]
        else:
            inventory = inventories[0]
            inventory.restocking_available = False
        response = self.client.put(f"{BASE_URL}/{inventory.id}/start_restock")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_stop_restock_an_inventory(self):
        """It should start restock for an inventory"""
        inventories = self._create_inventories(10)
        unavailable_inventories = [
            inventory
            for inventory in inventories
            if inventory.restocking_available is False
        ]
        inventory = unavailable_inventories[0]
        response = self.client.put(f"{BASE_URL}/{inventory.id}/stop_restock")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(f"{BASE_URL}/{inventory.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        logging.debug("Response data: %s", data)
        self.assertEqual(data["restocking_available"], True)

    def test_stop_restock_not_available(self):
        """It should not stop restock a Inventory that is available"""
        inventories = self._create_inventories(10)
        available_inventories = [
            inventory
            for inventory in inventories
            if inventory.restocking_available is True
        ]
        inventory = available_inventories[0]
        response = self.client.put(f"{BASE_URL}/{inventory.id}/stop_restock")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_start_restock_not_found(self):
        """It should not start restock a Inventory that is not existing"""
        response = self.client.put(f"{BASE_URL}/0/start_restock")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_stop_restock_not_found(self):
        """It should not stop restock a Inventory that is not existing"""
        response = self.client.put(f"{BASE_URL}/0/stop_restock")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ############################################################
    # Utility function to bulk create inventories
    ############################################################
    def _create_inventories(self, count: int = 1) -> list:
        """Factory method to create inventories in bulk"""
        inventories = []
        for _ in range(count):
            test_inventory = InventoryFactory()
            response = self.client.post(
                BASE_URL,
                json=test_inventory.serialize(),
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test inventory",
            )
            new_inventory = response.get_json()
            test_inventory.id = new_inventory["id"]
            inventories.append(test_inventory)
        return inventories


class TestSadPaths(TestCase):
    """Test REST Exception Handling"""

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()

    def test_method_not_allowed(self):
        """It test how the system handle a request with unexpected method"""
        response = self.client.put(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_internal_error(self):
        """It test that there is something wrong on server side"""
        response = self.client.get("api/error_test")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_not_found_error_handler(self):
        """It should test the not_found error handler"""
        # Make request to non-existent endpoint
        response = self.client.get("/non_existent_endpoint")

        # Assert the response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertEqual(data["status_code"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(data["error"], "URL Not Found")
        self.assertIn("message", data)

    ######################################################################
    #  T E S T   M O C K S
    ######################################################################

    @patch("service.routes.Inventory.find_by_name")
    def test_bad_request(self, bad_request_mock):
        """It should return a Bad Request error from Find By Name"""
        bad_request_mock.side_effect = DataValidationError()
        response = self.client.get(BASE_URL, query_string="name=fido")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("service.routes.Inventory.find_by_name")
    def test_mock_search_data(self, inventory_find_mock):
        """It should showing how to mock data"""
        inventory_find_mock.return_value = [
            MagicMock(serialize=lambda: {"name": "fido"})
        ]
        response = self.client.get(BASE_URL, query_string="name=fido")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
