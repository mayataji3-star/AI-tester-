"""Vertex AI express-mode Gemini adapter; credentials are read only from the environment.
Uses Python's standard library, so no additional SDK installation is needed.
"""
import json
import math
import os
import re
import time
from urllib import request, error
from pydantic import ValidationError


class ModelResponseError(RuntimeError):
    pass


class GeminiAPIError(RuntimeError):
    def __init__(self, message, http_status=None, retry_after_seconds=None, reason_code=None):
        self.reason_code = reason_code
        super().__init__(message + (f" [Google reason: {reason_code}]" if reason_code else ""))
        self.http_status = http_status
        self.retry_after_seconds = retry_after_seconds


class RateLimitError(GeminiAPIError):
    pass


class AuthenticationError(GeminiAPIError):
    pass


class NoRedirect(request.HTTPRedirectHandler):
    # Never forward an API-key header to a redirect destination.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def post_json(req, timeout):
    opener = request.build_opener(NoRedirect)
    with opener.open(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def safe_error(exc):
    """Extract only status/retry/reason information; never return raw service messages."""
    retry = None
    try:
        value = exc.headers.get('Retry-After') if exc.headers else None
        retry = float(value) if value is not None else None
    except (TypeError, ValueError):
        pass
    reason = None
    try:
        data = json.loads(exc.read().decode('utf-8'))
        for detail in data.get('error', {}).get('details', []):
            if detail.get('@type', '').endswith('RetryInfo'):
                delay = detail.get('retryDelay', '')
                if isinstance(delay, str) and delay.endswith('s'):
                    try:
                        retry = float(delay[:-1])
                    except ValueError:
                        pass
            if detail.get('@type', '').endswith('ErrorInfo'):
                reason = detail.get('reason')
    except (ValueError, OSError, AttributeError, TypeError):
        pass
    if not isinstance(reason, str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,63}', reason):
        reason = None
    if retry is not None and (not math.isfinite(retry) or retry < 0 or retry > 86400):
        retry = None
    if exc.code == 429:
        return RateLimitError('Gemini rate or quota limit reached. No paid fallback was attempted.', exc.code, retry, reason)
    if reason == 'SERVICE_DISABLED':
        return GeminiAPIError('Vertex AI service is disabled for this key or endpoint. Check the API service configuration with your trainer.', exc.code, reason_code=reason)
    if exc.code in (401, 403) or reason in ('API_KEY_INVALID', 'API_KEY_EXPIRED', 'API_KEY_SERVICE_BLOCKED'):
        return AuthenticationError('Gemini rejected the key or its permissions. Check the key locally with your trainer.', exc.code, reason_code=reason)
    if exc.code == 404:
        return GeminiAPIError('The configured Gemini model is unavailable for this key. Check config.json with your trainer.', exc.code, reason_code=reason)
    return GeminiAPIError('Gemini rejected the request. Check model access, API configuration, or service status.', exc.code, reason_code=reason)


def create_decider(config, instructions, decision_type, request_sender=None):
    if config.get('provider') != 'gemini':
        raise ValueError('Set provider to gemini in config.json.')
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if not key:
        raise ValueError('Set GEMINI_API_KEY locally; never put it in code or chat.')
    model = config['model']
    if not re.fullmatch(r'gemini-[A-Za-z0-9.-]+', model):
        raise ValueError('Use a Gemini model ID, such as gemini-3.5-flash-lite.')
    send = request_sender or post_json
    last_call = None
    timing = {"request_wait_seconds": 0.0, "api_request_seconds": 0.0, "api_requests": 0}

    def decide(task, observation, history, remaining):
        nonlocal last_call
        started = time.monotonic()
        if last_call is not None:
            delay = max(0, config.get('request_interval_seconds', 1) - (started-last_call))
            if delay >= remaining:
                raise TimeoutError('Task time budget exhausted before next Gemini request.')
            if delay:
                wait_started = time.monotonic()
                try:
                    time.sleep(delay)
                finally:
                    timing["request_wait_seconds"] += time.monotonic() - wait_started
        budget = remaining - (time.monotonic()-started)
        if budget <= 0:
            raise TimeoutError('Task time budget exhausted.')
        actions = [{k: item[k] for k in ('step', 'decision', 'tool_error') if k in item} for item in history]
        payload = {
            'systemInstruction': {'parts': [{'text': instructions}]},
            'contents': [{'role': 'user', 'parts': [{'text': json.dumps({
                'task': task, 'page': observation, 'actions': actions})}]}],
            'generationConfig': {
                'temperature': config['temperature'],
                'maxOutputTokens': config.get('max_completion_tokens', 2048),
                'responseMimeType': 'application/json',
                'responseJsonSchema': decision_type.model_json_schema(),
            },
        }
        req = request.Request(
            f'https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent',
            data=json.dumps(payload).encode('utf-8'), method='POST',
            headers={'Content-Type': 'application/json', 'x-goog-api-key': key})
        last_call = time.monotonic()
        timing["api_requests"] += 1
        try:
            response = send(req, timeout=max(0.1, min(45, budget)))
        except error.HTTPError as exc:
            raise safe_error(exc) from None
        except (error.URLError, OSError, ValueError):
            raise GeminiAPIError('Gemini connection failed or returned unreadable JSON. Check your connection and try later.') from None
        finally:
            timing["api_request_seconds"] += time.monotonic() - last_call
        candidates = response.get('candidates', [])
        if not candidates or candidates[0].get('finishReason') != 'STOP':
            raise ModelResponseError('Gemini response was blocked or incomplete; no browser action was executed.')
        text = ''.join(part.get('text', '') for part in candidates[0].get('content', {}).get('parts', [])
                       if not part.get('thought', False))
        try:
            decision = decision_type.model_validate_json(text, strict=True)
        except ValidationError:
            raise ModelResponseError('Gemini returned an invalid decision; no browser action was executed.') from None
        raw_usage = response.get('usageMetadata', {})
        usage = {
            'provider': 'gemini',
            'api_platform': 'vertex_ai_express',
            'prompt_tokens': raw_usage.get('promptTokenCount'),
            'completion_tokens': raw_usage.get('candidatesTokenCount'),
            'thinking_tokens': raw_usage.get('thoughtsTokenCount'),
            'total_tokens': raw_usage.get('totalTokenCount'),
            'response_model': response.get('modelVersion', model),
            'response_id': response.get('responseId'),
        }
        return decision, usage
    decide.timing = timing
    return decide
