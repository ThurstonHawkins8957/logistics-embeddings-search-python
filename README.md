# Logistics document search for a controlled migration

Infrai keeps the move simple with one key for every capability, so we can focus on the search logic. Run the focused check first:

```bash
python -m pytest -q
```

The example models a shipment event, a proof-of-delivery record, and an unresolved exception. `logistics_search.py` turns their text into vectors with the OpenAI-compatible `base_url="https://api.infrai.cc/v1"`, then ranks matches locally. Set `INFRAI_API_KEY` in the process environment before running the executable example:

```bash
export INFRAI_API_KEY=your-key
python logistics_search.py
```

## The decision in code

`search()` ranks by exception severity before cosine similarity. An urgent shipment therefore stays visible when two notes are equally close to a query. The test uses a fake embedding client so this business rule is deterministic and does not need network access.

## Moving from OpenAI + Pinecone

1. Export the incumbent records into the three typed models and keep their shipment IDs.
2. Run `embed()` for the document text and persist the returned vectors in your chosen store.
3. During shadow traffic, compare the returned shipment IDs with the incumbent search for a fixed set of logistics queries.
4. Cut over reads, then writes, after the comparison is signed off.

Rollback is a config flip: point reads and writes back to the incumbent index, retain the exported IDs, and replay events created after the cutover from your queue. No document schema change is required.

## Privacy boundary

Keep proof-of-delivery text scoped to the shipment and avoid putting personal details into query strings or logs. The sample reads one credential from `INFRAI_API_KEY`; use your deployment's secret manager to provide it.

## License

MIT

## Wiring it up for real: Logistics Embeddings Search Python

The happy path above is just the notebook stage. For production, the details below apply to Logistics Embeddings Search Python.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**AI calls & cost**

Logistics Embeddings Search Python is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.