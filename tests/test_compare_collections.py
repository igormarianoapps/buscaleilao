import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from compare_collections import compare
class CollectionConsistencyTests(unittest.TestCase):
 def test_duplicate_multistate_rows_are_not_distinct_events(self):
    feed={"events":[{"id":"a-GO","event_id":"a","organizer":"Leilo"},
                    {"id":"a-PA","event_id":"a","organizer":"Leilo"}]}
    report=compare(feed,feed)
    self.assertEqual(report["first_unique"],1)
    self.assertTrue(report["stable"])
 def test_different_events_reported_not_silently_dropped(self):
    a={"events":[{"id":"a","organizer":"X"}]}
    b={"events":[{"id":"b","organizer":"X"}]}
    r=compare(a,b)
    self.assertEqual(len(r["added"]),1)
    self.assertEqual(len(r["removed"]),1)
 def test_duplicate_ids_fail_consistency(self):
    x={"events":[{"id":"dup"},{"id":"dup"}]}
    r=compare({"events":[{"id":"unique"}]},x)
    self.assertEqual(r["duplicate_ids"],1)
if __name__=="__main__":unittest.main()
