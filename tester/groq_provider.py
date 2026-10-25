"""Groq-only model adapter. No OpenAI API connection or paid fallback."""
import json
import os
import time
from groq import Groq
from pydantic import ValidationError

class ModelResponseError(RuntimeError):
    """A model response could not be used as a browser decision."""


def create_decider(config, instructions, decision_type, client=None):
    if config.get('provider') != 'groq':
        raise ValueError('This tester supports provider=groq only.')
    if client is None:
        key = os.getenv('GROQ_API_KEY')
        if not key:
            raise ValueError('Set GROQ_API_KEY locally. Do not put it in code or chat.')
        client = Groq(api_key=key, max_retries=0)
    schema = decision_type.model_json_schema()
    last_call = None

    def decide(task, observation, history, remaining):
        nonlocal last_call
        started = time.monotonic()
        if last_call is not None:
            delay = max(0, config.get('request_interval_seconds', 3) - (started-last_call))
            if delay >= remaining:
                raise TimeoutError('Task budget exhausted before next model call.')
            if delay:
                time.sleep(delay)
        budget = remaining-(time.monotonic()-started)
        if budget <= 0:
            raise TimeoutError('Task budget exhausted.')
        # Actions and errors retain context without resending all previous page snapshots.
        actions = [{k: item[k] for k in ('step','decision','tool_error') if k in item}
                   for item in history]
        last_call = time.monotonic()
        response = client.chat.completions.create(
            model=config['model'], temperature=config['temperature'],
            max_completion_tokens=config.get('max_completion_tokens', 2048),
            timeout=max(0.1, min(45, budget)),
            messages=[{'role':'system','content':instructions},
                      {'role':'user','content':json.dumps({'task':task,'page':observation,'actions':actions})}],
            response_format={'type':'json_schema','json_schema':{
                'name':'browser_decision','strict':True,'schema':schema}})
        if not response.choices:
            raise ModelResponseError('Groq returned no choices.')
        choice = response.choices[0]
        if choice.finish_reason != 'stop':
            raise ModelResponseError('Incomplete model response; no action executed.')
        if getattr(choice.message, 'refusal', None) or not choice.message.content:
            raise ModelResponseError('Model refused or returned empty content; no action executed.')
        try:
            decision = decision_type.model_validate_json(choice.message.content, strict=True)
        except ValidationError:
            raise ModelResponseError('Invalid decision schema; no action executed.') from None
        tokens = response.usage.model_dump() if response.usage else {}
        tokens['response_model'] = response.model
        tokens['system_fingerprint'] = getattr(response, 'system_fingerprint', None)
        return decision, tokens
    return decide
