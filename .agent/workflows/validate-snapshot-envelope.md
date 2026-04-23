---
description: Validate that a snapshot file matches the common envelope
---
1. Read the file at the given path
2. Check it has: dataset, source, fetched_at, as_of, status, record_count, data
3. Check data is an array
4. Check each record matches the expected contract for that dataset
5. Report validation result
