### Upsert 
- Upsert is a combination of update and insert
- It allows you to update an existing row or insert a new one if it doesn't exist

##### Session 1
```
# Consider a table test_locks (id, data) with values (1, 'Row1'), (2, 'Row2'), (3, 'Row3') and we want to manipulate row with id = 1.

INSERT INTO test_locks (id, data) VALUES (1, 'Row 11') ON CONFLICT (id) DO UPDATE SET data = 'Row 11';

# Result: test_locks (id, data) with values (1, 'Row11'), (2, 'Row2'), (3, 'Row3')
```