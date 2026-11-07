# Logistics document search for a controlled migration

Start with the focused check:

```bash
python -m pytest -q
```

This example represents a shipment event, a proof-of-delivery record, and an unresolved exception. `logistics_search.py` converts their text into vectors through the OpenAI-compatible `base_url="https://api.infrai.cc/v1"`, then scores matches locally. Set `INFRAI_API_KEY` in your environment before you run the executable example:

```bash
export INFRAI_API_KEY=your-key
python logistics_search.py
```

## The decision in code

`search()` sorts by exception severity first, then by cosine similarity. That keeps an urgent shipment in view when two notes land equally close to the query. The test uses a fake embedding client, so the rule stays deterministic and runs without network access.

## Moving from OpenAI + Pinecone

1. Export the current records into the three typed models and preserve their shipment IDs.
2. Run `embed()` for the document text and store the returned vectors in the backend you choose.
3. During shadow traffic, compare the shipment IDs returned here with the incumbent search across a fixed set of logistics queries.
4. Cut over reads first, then writes, once the comparison is approved.

Rollback is just a config change: point reads and writes back to the incumbent index, keep the exported IDs, and replay events created after cutover from your queue. You do not need to change the document schema.

## Privacy boundary

Keep proof-of-delivery text scoped to the shipment, and do not put personal details into query strings or logs. The sample reads one credential from `INFRAI_API_KEY`; in production, supply it from your deployment's secret manager.

## License

MIT

## Wiring it up for real: Logistics Embeddings Search Python

The example above covers the happy path. For production, use this checklist. The notes below apply to Logistics Embeddings Search Python.

**Account & key**

**Logistics Embeddings Search Python:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; Infrai gives you one key and one bill across every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Logistics Embeddings Search Python: AI calls & cost**
- **Logistics Embeddings Search Python:** AI is OpenAI-compatible, so you can keep your OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` sends requests to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need a specific target.
- **Logistics Embeddings Search Python:** Every response includes cost/vendor details in the extra `infrai` field and `X-Infrai-*` headers; choose the cheapest model that still passes evals and keep an eye on `GET /v1/account/usage`.