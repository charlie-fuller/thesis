# /test - Run Backend Tests

Run the thesis backend test suite efficiently.

## Usage
```
/test              # Run all tests
/test unit         # Run only unit tests
/test integration  # Run only integration tests
/test <pattern>    # Run tests matching pattern
```

## How to Execute

### All Tests
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
./run_tests.sh
```

### Unit Tests Only
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
.venv/bin/python -m pytest tests/ --ignore=tests/test_integration.py -v --tb=short -q
```

### Integration Tests Only
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
.venv/bin/python -m pytest tests/test_integration.py -v
```

### Specific Test Pattern
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
.venv/bin/python -m pytest tests/ -k "<pattern>" -v
```

## Test Categories

| Category | Marker | Description |
|----------|--------|-------------|
| Unit tests | default | Fast tests, no DB required |
| Integration | `test_integration.py` | Real DB, use `--forked` |
| Smoke tests | `test_smoke.py` | Basic endpoint checks |
| Security tests | `test_security.py` | Auth and security |

## Expected Results

- **Unit tests**: ~770 passed, ~36 xfailed (expected failures for unimplemented features)
- **Integration tests**: ~35 passed

## Troubleshooting

If tests fail with module import errors, check:
1. You're in the `/backend` directory
2. Using `.venv/bin/python` not system python
3. `.env` file exists with credentials

## Lessons Learned Reference

See `docs/testing/LESSONS_LEARNED.md` for common test issues and fixes.
