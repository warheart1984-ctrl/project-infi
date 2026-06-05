"""Tests for operator JWT authentication on the workflow shell."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import app.config as config
import app.db as db
import app.main as main


class OperatorAuthTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        self.original_bearer = config.APP_BEARER_TOKEN
        self.original_auth_required = config.AUTH_REQUIRED
        self.original_allow_registration = config.ALLOW_OPERATOR_REGISTRATION
        self.prior_genome_boot = os.environ.get("AAIS_GENOME_BOOT")
        os.environ["AAIS_GENOME_BOOT"] = "warn"

        db.DB_PATH = Path(self.tempdir.name) / "operator-auth.db"
        config.APP_BEARER_TOKEN = ""
        config.AUTH_REQUIRED = False
        config.ALLOW_OPERATOR_REGISTRATION = True
        db.init_db()

    def tearDown(self):
        config.APP_BEARER_TOKEN = self.original_bearer
        config.AUTH_REQUIRED = self.original_auth_required
        config.ALLOW_OPERATOR_REGISTRATION = self.original_allow_registration
        db.DB_PATH = self.original_db_path
        if self.prior_genome_boot is None:
            os.environ.pop("AAIS_GENOME_BOOT", None)
        else:
            os.environ["AAIS_GENOME_BOOT"] = self.prior_genome_boot
        self.tempdir.cleanup()

    def test_auth_not_required_without_users(self):
        with TestClient(main.app) as client:
            response = client.get("/auth/status")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertFalse(payload["auth_required"])
            self.assertTrue(payload["registration_allowed"])

            protected = client.get("/workflows")
            self.assertEqual(protected.status_code, 200)

    def test_register_login_and_access_protected_route(self):
        with TestClient(main.app) as client:
            register = client.post(
                "/auth/register",
                json={"username": "operator.one", "password": "secure-pass-1"},
            )
            self.assertEqual(register.status_code, 200)
            tokens = register.json()
            self.assertTrue(tokens["access_token"])
            self.assertTrue(tokens["refresh_token"])
            self.assertEqual(tokens["user"]["username"], "operator.one")
            self.assertEqual(tokens["user"]["role"], "admin")

            status = client.get("/auth/status")
            self.assertTrue(status.json()["auth_required"])

            unauthorized = client.get("/workflows")
            self.assertEqual(unauthorized.status_code, 401)

            authorized = client.get(
                "/workflows",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            self.assertEqual(authorized.status_code, 200)

            me = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            self.assertEqual(me.status_code, 200)
            self.assertEqual(me.json()["username"], "operator.one")

    def test_refresh_issues_new_access_token(self):
        with TestClient(main.app) as client:
            register = client.post(
                "/auth/register",
                json={"username": "refresh.user", "password": "secure-pass-2"},
            )
            tokens = register.json()

            refreshed = client.post(
                "/auth/refresh",
                json={"refresh_token": tokens["refresh_token"]},
            )
            self.assertEqual(refreshed.status_code, 200)
            refreshed_tokens = refreshed.json()
            self.assertTrue(refreshed_tokens["access_token"])

            authorized = client.get(
                "/workflows",
                headers={"Authorization": f"Bearer {refreshed_tokens['access_token']}"},
            )
            self.assertEqual(authorized.status_code, 200)

    def test_legacy_bearer_token_still_works(self):
        config.APP_BEARER_TOKEN = "legacy-shared-secret"

        with TestClient(main.app) as client:
            status = client.get("/auth/status")
            self.assertTrue(status.json()["auth_required"])

            unauthorized = client.get("/workflows")
            self.assertEqual(unauthorized.status_code, 401)

            authorized = client.get(
                "/workflows",
                headers={"Authorization": "Bearer legacy-shared-secret"},
            )
            self.assertEqual(authorized.status_code, 200)

    @patch.object(main.run_workflow_job, "delay")
    def test_login_rejects_invalid_password(self, _delay_mock):
        with TestClient(main.app) as client:
            client.post(
                "/auth/register",
                json={"username": "valid.user", "password": "secure-pass-3"},
            )
            response = client.post(
                "/auth/login",
                json={"username": "valid.user", "password": "wrong-password"},
            )
            self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
