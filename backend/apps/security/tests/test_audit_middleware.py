# -*- coding: utf-8 -*-
import json
import time

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

import apps.security.services as security_services
from apps.security.middleware import AuditLogMiddleware, RequestSignatureMiddleware
from apps.security.models import AuditLog
from apps.security.services import SignatureService


def _ok_view(request):
    return HttpResponse('{"code":0}', content_type="application/json")


class AuditLogMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(
        SECURITY_AUDIT_ENABLED=True,
        SECURITY_SIGNATURE_ENABLED=False,
        SECURITY_RATE_LIMIT_ENABLED=False,
    )
    def test_post_request_writes_audit_log(self):
        middleware = AuditLogMiddleware(_ok_view)
        request = self.factory.post(
            "/api/creation/submit/",
            data='{"theme":"x"}',
            content_type="application/json",
        )
        before = AuditLog.objects.count()
        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(AuditLog.objects.count(), before)


class SignatureTamperTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        security_services._default_signature = None

    @override_settings(
        SECURITY_SIGNATURE_ENABLED=True,
        API_SIGN_SECRET="unit-test-sign-secret-32bytes!!",
        SECURITY_SIGNATURE_SKIP_PATHS=("/admin/", "/static/", "/media/", "/health/"),
    )
    def test_tampered_body_hash_rejected(self):
        middleware = RequestSignatureMiddleware(_ok_view)
        path = "/api/users/me/"
        body = b'{"tampered": true}'
        signer = SignatureService(secret="unit-test-sign-secret-32bytes!!")
        headers = signer.generate_headers("POST", path, body=b'{"original": true}')
        request = self.factory.post(
            path,
            data=body,
            content_type="application/json",
            **{f"HTTP_{k.replace('-', '_').upper()}": v for k, v in headers.items()},
        )
        response = middleware(request)
        self.assertEqual(response.status_code, 401)

    @override_settings(
        SECURITY_SIGNATURE_ENABLED=True,
        API_SIGN_SECRET="unit-test-sign-secret-32bytes!!",
        SECURITY_SIGNATURE_SKIP_PATHS=("/admin/", "/static/", "/media/", "/health/"),
    )
    def test_expired_timestamp_rejected(self):
        middleware = RequestSignatureMiddleware(_ok_view)
        path = "/api/users/me/"
        signer = SignatureService(secret="unit-test-sign-secret-32bytes!!")
        expired_ts = int(time.time()) - 3600
        nonce = "abc123def4567890"
        body_hash = signer.compute_body_hash(None)
        signature = signer.sign("GET", path, expired_ts, nonce, body_hash)
        request = self.factory.get(
            path,
            HTTP_X_TIMESTAMP=str(expired_ts),
            HTTP_X_NONCE=nonce,
            HTTP_X_SIGNATURE=signature,
            HTTP_X_BODY_HASH=body_hash,
        )
        response = middleware(request)
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.content)
        self.assertEqual(body["code"], 40101)
