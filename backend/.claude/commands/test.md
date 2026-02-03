# /test - Run Backend Tests

Run the thesis backend test suite efficiently.

## Usage
```
/test              # Run all tests
/test unit         # Run only unit tests
/test integration  # Run only integration tests
/test helpers      # Run refactored helper tests
/test <pattern>    # Run tests matching pattern
```

## How to Execute

**IMPORTANT**: The .env file is encrypted with dotenvx. Use the dotenvx wrapper for all test commands.

### Recommended: Use run_all_tests.sh
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
./scripts/run_all_tests.sh
```

### Quick Mode (core tests only)
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
./scripts/run_all_tests.sh --quick
```

### Unit Tests Only
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest tests/ --ignore=tests/test_integration.py -v --tb=short -q
```

### Integration Tests Only
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest tests/test_integration.py -v
```

### Refactored Helper Tests
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest tests/test_refactored_helpers.py -v
```

### Specific Test Pattern
```bash
cd /Users/charlie.fuller/vaults/Contentful/GitHub/thesis/backend
DOTENV_PRIVATE_KEY=4980b243281755774eab2a5107d475ceecdeceb0b7aef97e014d9cfcece1c230 \
dotenvx run -f .env -- .venv/bin/python -m pytest tests/ -k "<pattern>" -v
```

## Test Categories

| Category | File | Description | Test Count |
|----------|------|-------------|------------|
| Unit tests | `test_*.py` | Fast tests, mocked DB | ~770 |
| Integration | `test_integration.py` | Real DB, live API | ~35 |
| Smoke tests | `test_smoke.py` | Basic endpoint checks | ~20 |
| Security tests | `test_security.py` | Auth and security | ~15 |
| Refactored helpers | `test_refactored_helpers.py` | Helper method tests | ~62 |

## Expected Results

- **Unit tests**: ~770 passed, ~36 xfailed (expected failures for unimplemented features)
- **Integration tests**: ~35 passed
- **Helper tests**: ~62 passed

## Troubleshooting

If tests fail with module import errors, check:
1. You're in the `/backend` directory
2. Using `.venv/bin/python` not system python
3. Using dotenvx to decrypt `.env`

If tests fail with "Missing env variable" errors:
- Ensure DOTENV_PRIVATE_KEY is set correctly
- Check that dotenvx is installed: `which dotenvx`

## Lessons Learned Reference

See `docs/testing/LESSONS_LEARNED.md` for common test issues and fixes.
