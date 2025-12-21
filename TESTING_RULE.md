# Pre-Commit Testing Rule

## Rule: Always Test Before Commit

Before committing any code changes, especially fixes:

1. **Create a test script** to verify the fix works
2. **Run the test** and ensure it passes
3. **Clean up test files** (delete or ensure they're gitignored)
4. **Only commit if tests pass**

## Test File Management:

### Naming Convention (Auto-ignored):
- `test_*.py` - Test files (gitignored)
- `*_test.py` - Test files (gitignored) 
- `tests/temp_*.py` - Temporary test files (gitignored)

### Before Commit:
- ✅ Verify test files are in `.gitignore`
- ✅ Delete temporary test files OR ensure they match ignore patterns
- ✅ Never commit test files to main repository

## Test Types by Change:

### API/Function Changes
- Create isolated test for the specific function
- Test edge cases (Hebrew chars, empty strings, etc.)
- Verify expected behavior vs actual behavior

### Logic Changes  
- Test the core logic with sample inputs
- Verify both positive and negative cases
- Ensure no regressions

### Integration Changes
- Test the full workflow if possible
- Check that components work together
- Verify error handling

## Example Test Structure:
```python
def test_feature():
    # Test cases
    test_cases = [
        (input1, expected1),
        (input2, expected2),
    ]
    
    for input_val, expected in test_cases:
        result = function_to_test(input_val)
        assert result == expected, f"Failed for {input_val}"
    
    print("All tests passed!")
```

## Commit Checklist:
- ✅ Tests created
- ✅ Tests run successfully  
- ✅ Logic verified correct
- ✅ No regressions detected
- ✅ Test files cleaned up/gitignored
- ✅ Only production code committed