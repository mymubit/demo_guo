# -*- coding: utf-8 -*-
import json

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

import apps.security.services as security_services
from apps.security.middleware import RateLimitMiddleware, RequestSignatureMiddleware
from apps.security.services import RateLimitPolicy, RateLimitService, SignatureService


def _ok_view(request):
    return HttpResponse('{"code":0}', content_type="application/json")


class RequestSignatureMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        security_services._default_signature = None

    @override_settings(
        SECURITY_SIGNATURE_ENABLED=True,
        API_SIGN_SECRET="unit-test-sign-secret-32bytes!!",
        SECURITY_SIGNATURE_SKIP_PATHS=("/admin/", "/static/", "/media/", "/health/"),
    )
    def test_missing_signature_returns_401(self):
        middleware = RequestSignatureMiddleware(_ok_view)
        request = self.factory.get("/api/users/me/")
        response = middleware(request)
        self.assertEqual(response.status_code, 401)
        body = json.loads(response.content)
        self.assertEqual(body["code"], 40101)

    @override_settings(
        SECURITY_SIGNATURE_ENABLED=True,
        API_SIGN_SECRET="unit-test-sign-secret-32bytes!!",
        SECURITY_SIGNATURE_SKIP_PATHS=("/admin/", "/static/", "/media/", "/health/"),
    )
    def test_valid_signature_passes_through(self):
        middleware = RequestSignatureMiddleware(_ok_view)
        path = "/api/users/me/"
        signer = SignatureService(secret="unit-test-sign-secret-32bytes!!")
        headers = signer.generate_headers("GET", path)
        request = self.factory.get(path, **{f"HTTP_{k.replace('-', '_').upper()}": v for k, v in headers.items()})
        response = middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(SECURITY_SIGNATURE_ENABLED=False)
    def test_signature_disabled_skips_verification(self):
        middleware = RequestSignatureMiddleware(_ok_view)
        request = self.factory.get("/api/users/me/")
        response = middleware(request)
        self.assertEqual(response.status_code, 200)


class RateLimitMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        security_services._default_rate_limit = None

    @override_settings(SECURITY_RATE_LIMIT_ENABLED=True)
    def test_rate_limit_blocks_after_threshold(self):
        middleware = RateLimitMiddleware(_ok_view)
        middleware._rate_limit = RateLimitService(
            policy=RateLimitPolicy(anon_limit=2, default_limit=2, default_window=60, anon_window=60)
        )
        path = "/api/works/"
        for _ in range(2):
            request = self.factory.get(path, REMOTE_ADDR="10.0.0.1")
            response = middleware(request)
            self.assertEqual(response.status_code, 200)
        request = self.factory.get(path, REMOTE_ADDR="10.0.0.1")
        response = middleware(request)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(json.loads(response.content)["code"], 42901)

    @override_settings(SECURITY_RATE_LIMIT_ENABLED=False)
    def test_rate_limit_disabled_allows_requests(self):
        middleware = RateLimitMiddleware(_ok_view)
        path = "/api/works/"
        for _ in range(5):
            request = self.factory.get(path, REMOTE_ADDR="10.0.0.2")
            response = middleware(request)
            self.assertEqual(response.status_code, 200)
