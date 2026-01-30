# QA Import Guide

This guide explains how to import QA (Question-Answer) pairs into Helix. QA pairs form the knowledge base used for RAG (Retrieval-Augmented Generation) responses.

## Supported Formats

Helix supports three import formats:

1. **CSV** - Comma-separated values
2. **JSON** - JavaScript Object Notation
3. **Text** - Plain text with delimiters

---

## CSV Format

### Requirements

- UTF-8 encoding
- Header row required
- Columns: `question`, `answer`, `category` (optional)

### Example

```csv
question,answer,category
What are your store hours?,We are open Monday to Friday from 9 AM to 6 PM.,Hours
How do I return an item?,Returns are accepted within 30 days with receipt.,Returns
Where are you located?,We have locations in Manila and Cebu.,Locations
```

### Import via API

```bash
curl -X POST "https://helix-api.example.com/qa/import/csv" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@qa_pairs.csv"
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Encoding errors | Save file as UTF-8 |
| Missing columns | Ensure header has `question` and `answer` |
| Empty rows | Remove blank lines from file |
| Quotes in text | Use double quotes: `"He said ""hello"""` |

---

## JSON Format

### Requirements

- UTF-8 encoding
- Array of objects
- Each object must have `question` and `answer` fields

### Example

```json
[
  {
    "question": "What are your store hours?",
    "answer": "We are open Monday to Friday from 9 AM to 6 PM.",
    "category": "Hours"
  },
  {
    "question": "How do I return an item?",
    "answer": "Returns are accepted within 30 days with receipt.",
    "category": "Returns",
    "tags": ["policy", "returns"]
  }
]
```

### Import via API

```bash
curl -X POST "https://helix-api.example.com/qa/import/json" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @qa_pairs.json
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Invalid JSON | Validate with `jq . qa_pairs.json` |
| Missing required fields | Ensure each object has `question` and `answer` |
| Encoding issues | Use UTF-8 encoding |

---

## Text Format

### Requirements

- UTF-8 encoding
- Question and answer separated by `---`
- Pairs separated by blank line

### Example

```text
What are your store hours?
---
We are open Monday to Friday from 9 AM to 6 PM.

How do I return an item?
---
Returns are accepted within 30 days with receipt.
```

### Import via API

```bash
curl -X POST "https://helix-api.example.com/qa/import/text" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: text/plain" \
  --data-binary @qa_pairs.txt
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Wrong delimiter | Use exactly `---` on its own line |
| Missing blank lines | Ensure pairs are separated by empty line |
| Extra whitespace | Trim leading/trailing spaces |

---

## Validation Rules

### Question Requirements

- Minimum length: 5 characters
- Maximum length: 1,000 characters
- Must end with `?` (recommended but not required)
- No duplicate questions within same import

### Answer Requirements

- Minimum length: 10 characters
- Maximum length: 10,000 characters
- Plain text or Markdown supported
- No HTML allowed

### Category Requirements

- Maximum length: 100 characters
- Alphanumeric and spaces only
- Case-insensitive matching

---

## Sample Files

Download sample files from the repository:

- [`samples/qa_import_sample.csv`](../samples/qa_import_sample.csv)
- [`samples/qa_import_sample.json`](../samples/qa_import_sample.json)
- [`samples/qa_import_sample.txt`](../samples/qa_import_sample.txt)

---

## Import Status

After import, check the status:

```bash
curl "https://helix-api.example.com/qa/import/status/{import_id}" \
  -H "X-API-Key: your-api-key"
```

Response:

```json
{
  "import_id": "abc123",
  "status": "completed",
  "total_rows": 100,
  "imported": 98,
  "skipped": 2,
  "errors": [
    {"row": 45, "error": "Duplicate question"},
    {"row": 67, "error": "Answer too short"}
  ]
}
```

---

## Embedding Generation

After import, embeddings are generated automatically in the background. Check embedding status:

```bash
curl "https://helix-api.example.com/qa/pairs?embedding_status=pending" \
  -H "X-API-Key: your-api-key"
```

Embedding generation typically takes:

- 1-10 pairs: < 5 seconds
- 10-100 pairs: < 30 seconds
- 100-1000 pairs: 1-5 minutes

---

## Best Practices

1. **Start small** - Import 10-20 pairs first to verify format
2. **Use categories** - Organize QA pairs for easier management
3. **Keep answers concise** - Aim for 50-200 words per answer
4. **Avoid duplicates** - Check for existing questions before import
5. **Test responses** - Verify imported pairs work in chat

---

## Troubleshooting

### Import fails with "Invalid format"

- Verify file encoding is UTF-8
- Check for BOM (Byte Order Mark) - remove if present
- Validate JSON/CSV syntax

### Embeddings not generating

- Check OpenAI API key is configured
- Verify API quota is not exceeded
- Check background job logs

### Duplicates not detected

- Duplicate detection is case-insensitive
- Check for invisible characters in questions
- Use the deduplication endpoint before import

---

*Last updated: January 2026*
