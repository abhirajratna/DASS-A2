# StreetRace Manager Integration Testing Report

## Modules implemented

Required modules:
- Registration module
- Crew Management module
- Inventory module
- Race Management module
- Results module
- Mission Planning module

Additional modules:
- Vehicle Maintenance module: repairs damaged cars, checks mechanic availability, and updates cash with repair cost.
- Reputation module: tracks crew reputation after races and missions.

## Integration test cases

| Test ID | Scenario being tested | Modules involved | Why this case is needed | Expected result | Actual result | Errors/logical issues found |
|---|---|---|---|---|---|---|
| IT-01 | Register a member as driver and enter race | Registration, Crew Management, Inventory, Race Management | Validates the normal end-to-end path for race entry | Registered driver with valid car should be accepted into race | Pass: race created with correct driver and car | None |
| IT-02 | Try race entry with unregistered driver | Race Management, Crew Management, Registration | Ensures business rule "member must be registered first" is enforced | System should reject race creation with clear error | Pass: `ValueError` raised with "not registered" | None |
| IT-03 | Complete race and verify result + money flow | Race Management, Results, Inventory | Checks data flow from race completion into rankings and cash balance | Race should be marked completed, ranking points updated, prize added to inventory cash | Pass: status/position updated, ranking points = 10, cash increased | None |
| IT-04 | Damaged car followed by mechanic-required mission | Results, Inventory, Mission Planning, Crew Management | Validates dependency rule after damage event and role validation for mission | Mission requiring mechanic should fail if mechanic absent, then pass after mechanic is assigned | Pass: first mission rejected, second mission starts with mechanic assignment | None |
| IT-05 | Mission start with missing required role | Mission Planning, Crew Management, Registration | Confirms mission cannot proceed when any required role is unavailable | Mission should not start and must show missing role | Pass: `ValueError` raised mentioning missing `strategist` role | None |

## Implemented fixes observed during integration

1. Import resolution issue in test environment:
   - Issue: test runner could not import package path for integration code.
   - Fix: added `integration/tests/conftest.py` to include `integration/code` in `sys.path`.

2. Driver validation correctness in race creation:
   - Issue: race entry logic originally checked for existence of any driver, not necessarily selected driver.
   - Fix: added `member_has_role(name, role)` in Crew Management and used it in Race Management.

## Execution summary

- Test file: `integration/tests/test_streetrace_integration.py`
- Command used: `pytest -q integration/tests/test_streetrace_integration.py`
- Result: `5 passed`
