# API/Interface Specification: Default Stock ID Change

## Function Parameter Changes

The following common patterns will be updated:

### Example Function Signature Update
```python
# Before
def test_some_rule(stock_id='2330', days=180):
    ...

# After
def test_some_rule(stock_id='00631L', days=180):
    ...
```

### Example Input Prompt Update
```python
# Before
stock_id = input("\n請輸入股票代碼 (預設2330): ").strip() or '2330'

# After
stock_id = input("\n請輸入股票代碼 (預設00631L): ").strip() or '00631L'
```

### Example Fallback Logic
```python
# Before
if not sid: sid = '2330'

# After
if not sid: sid = '00631L'
```
