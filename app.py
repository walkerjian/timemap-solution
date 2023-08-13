import datetime

# User class representing actors who can perform operations
class User:
    def __init__(self, name):
        self.name = name

# EventLogDB mimics a database table for event logs
class EventLogDB:
    def __init__(self):
        self.table = []
        self.id_counter = 0
    
    def create(self, key, value):
        timestamp = datetime.datetime.utcnow().isoformat()
        self.table.append({
            "id": self.id_counter,
            "key": key,
            "value": value,
            "timestamp": timestamp
        })
        self.id_counter += 1
    
    def read(self, key, timestamp=None):
        if timestamp:
            return [entry for entry in self.table if entry["key"] == key and entry["timestamp"] <= timestamp]
        return [entry for entry in self.table if entry["key"] == key]

# AuditLogDB mimics a database table for audit logs (Pig's Ear)
class AuditLogDB:
    def __init__(self):
        self.table = []
    
    def log(self, user, action, key, value=None):
        timestamp = datetime.datetime.utcnow().isoformat()
        self.table.append({
            "user": user.name,
            "action": action,
            "key": key,
            "value": value,
            "timestamp": timestamp
        })

# TimeMapDBWithAudit is the main class interfacing with the above databases
class TimeMapDBWithAudit:
    def __init__(self):
        self.db = EventLogDB()
        self.audit_db = AuditLogDB()
    
    def set(self, user, key, value, time=None):
        try:
            self.db.create(key, value)
            if time:
                self.db.table[-1]["timestamp"] = time.isoformat()
            self.audit_db.log(user, "set", key, value)
        except Exception as e:
            raise e
    
    def get(self, user, key, time):
        try:
            entries = self.db.read(key, time.isoformat())
            value = None if not entries else sorted(entries, key=lambda x: x["timestamp"], reverse=True)[0]["value"]
            self.audit_db.log(user, "get", key, value)
            return value
        except Exception as e:
            raise e
    
    def tombstone(self, user, key):
        try:
            self.db.create(key, "TOMBSTONED")
            self.audit_db.log(user, "tombstone", key)
        except Exception as e:
            raise e

# Testing the new approach with audit logging
def test_TimeMapDBWithAudit():
    user1 = User("Alice")
    user2 = User("Bob")

    d = TimeMapDBWithAudit()

    # Test 1
    d.set(user1, 1, 1, datetime.datetime.utcnow())
    assert len(d.audit_db.table) == 1, "Test 1 Failed"
    
    # Test 2
    assert d.get(user2, 1, datetime.datetime.utcnow()) == 1, "Test 2 Failed"
    assert len(d.audit_db.table) == 2, "Test 2 Failed"
    
    # Test 3
    d.tombstone(user1, 1)
    assert d.get(user2, 1, datetime.datetime.utcnow()) == "TOMBSTONED", "Test 3 Failed"
    assert len(d.audit_db.table) == 4, "Test 3 Failed"
    
    # Test 4
    d.set(user2, 1, 2, datetime.datetime.utcnow())
    assert d.get(user1, 1, datetime.datetime.utcnow()) == 2, "Test 4 Failed"
    
    # Test 5: Tombstoning again
    d.tombstone(user1, 1)
    assert d.get(user2, 1, datetime.datetime.utcnow()) == "TOMBSTONED", "Test 5 Failed"
    
    print("All tests passed!")

test_TimeMapDBWithAudit()

def display_tables(d):
    """
    Display the contents of the EventLogDB and AuditLogDB tables.
    """
    print("\nEventLogDB Table:")
    for entry in d.db.table:
        print(entry)
    
    print("\nAuditLogDB Table:")
    for entry in d.audit_db.table:
        print(entry)
    print("\n----------\n")

def test_TimeMapDBWithAudit_detailed():
    user1 = User("Alice")
    user2 = User("Bob")
    
    d = TimeMapDBWithAudit()
    
    # Initial state
    print("Initial State:")
    display_tables(d)
    
    # Test 1: user1 sets a value
    d.set(user1, 1, 1, datetime.datetime.utcnow())
    print("After user1 sets key 1 to value 1:")
    display_tables(d)
    
    # Test 2: user2 retrieves that value
    d.get(user2, 1, datetime.datetime.utcnow())
    print("After user2 gets key 1:")
    display_tables(d)
    
    # Test 3: user1 tombstones the key
    d.tombstone(user1, 1)
    print("After user1 tombstones key 1:")
    display_tables(d)
    
    # Test 4: user2 retrieves the tombstoned key
    d.get(user2, 1, datetime.datetime.utcnow())
    print("After user2 gets tombstoned key 1:")
    display_tables(d)
    
    # Test 5: user2 sets a new value for the tombstoned key
    d.set(user2, 1, 2, datetime.datetime.utcnow())
    print("After user2 sets key 1 to value 2:")
    display_tables(d)
    
    # Test 6: user1 retrieves the newly set value
    d.get(user1, 1, datetime.datetime.utcnow())
    print("After user1 gets key 1:")
    display_tables(d)
    
    # Adapting the original test examples you provided
    d.set(user1, 1, 1, datetime.datetime.utcnow())
    print("After setting key 1 to value 1 (timestamp = now):")
    display_tables(d)

    time_2 = datetime.datetime.utcnow() + datetime.timedelta(seconds=2)
    d.set(user2, 1, 2, time_2)
    print(f"After setting key 1 to value 2 (timestamp = {time_2}):")
    display_tables(d)
    
    time_1 = datetime.datetime.utcnow() + datetime.timedelta(seconds=1)
    d.get(user1, 1, time_1)
    print(f"After getting key 1 at timestamp {time_1}:")
    display_tables(d)
    
    time_3 = datetime.datetime.utcnow() + datetime.timedelta(seconds=3)
    d.get(user2, 1, time_3)
    print(f"After getting key 1 at timestamp {time_3}:")
    display_tables(d)

test_TimeMapDBWithAudit_detailed()


import pandas as pd

class TimeMapPandas:
    def __init__(self):
        # EventLog DataFrame
        self.event_log = pd.DataFrame(columns=['id', 'key', 'value', 'timestamp'])
        self.event_log_id_counter = 0

        # AuditLog DataFrame
        self.audit_log = pd.DataFrame(columns=['user', 'action', 'key', 'value', 'timestamp'])
    
    def set(self, user, key, value, time=None):
        timestamp = datetime.datetime.utcnow() if not time else time
        new_entry = {'id': self.event_log_id_counter, 'key': key, 'value': value, 'timestamp': timestamp}
        self.event_log = self.event_log.append(new_entry, ignore_index=True)
        
        self.audit_log = self.audit_log.append({
            'user': user.name, 'action': 'set', 'key': key, 'value': value, 'timestamp': timestamp
        }, ignore_index=True)
        
        self.event_log_id_counter += 1

    def get(self, user, key, time):
        filtered_entries = self.event_log[
            (self.event_log['key'] == key) & (self.event_log['timestamp'] <= time)
        ]
        
        if filtered_entries.empty:
            value = None
        else:
            value = filtered_entries.sort_values(by='timestamp', ascending=False).iloc[0]['value']
        
        self.audit_log = self.audit_log.append({
            'user': user.name, 'action': 'get', 'key': key, 'value': value, 'timestamp': datetime.datetime.utcnow()
        }, ignore_index=True)
        
        return value
    
    def tombstone(self, user, key):
        timestamp = datetime.datetime.utcnow()
        new_entry = {'id': self.event_log_id_counter, 'key': key, 'value': 'TOMBSTONED', 'timestamp': timestamp}
        self.event_log = self.event_log.append(new_entry, ignore_index=True)
        
        self.audit_log = self.audit_log.append({
            'user': user.name, 'action': 'tombstone', 'key': key, 'value': None, 'timestamp': timestamp
        }, ignore_index=True)
        
        self.event_log_id_counter += 1

# Testing the pandas approach
def test_TimeMapPandas():
    user1 = User("Alice")
    user2 = User("Bob")
    
    d = TimeMapPandas()
    d.set(user1, 1, 1, datetime.datetime.utcnow())
    assert len(d.audit_log) == 1, "Test 1 Failed"
    
    assert d.get(user2, 1, datetime.datetime.utcnow()) == 1, "Test 2 Failed"
    assert len(d.audit_log) == 2, "Test 2 Failed"
    
    d.tombstone(user1, 1)
    assert d.get(user2, 1, datetime.datetime.utcnow()) == "TOMBSTONED", "Test 3 Failed"
    assert len(d.audit_log) == 4, "Test 3 Failed"
    
    d.set(user2, 1, 2, datetime.datetime.utcnow())
    assert d.get(user1, 1, datetime.datetime.utcnow()) == 2, "Test 4 Failed"
    
    d.tombstone(user1, 1)
    assert d.get(user2, 1, datetime.datetime.utcnow()) == "TOMBSTONED", "Test 5 Failed"
    
    print("All tests passed!")

test_TimeMapPandas()
