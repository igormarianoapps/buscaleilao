import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from platform_review import build
class PlatformReviewTests(unittest.TestCase):
 def test_rejects_individual_lots_categories_and_nonvehicles(self):
    items=[
        {"url_kind":"individual_lot_not_auction","category_hint":"vehicle"},
        {"url_kind":"generic_category_not_auction","category_hint":"vehicle"},
        {"url_kind":"candidate_direct","category_hint":"non_vehicle"},
        {"url_kind":"candidate_direct","category_hint":"vehicle","date_hint":"2026-11-24","state_hint_verified_from_event":"DF"}
    ]
    x=build({"platforms":{"parque":{"candidates":items}}})
    self.assertEqual(x["candidates_count"],1)
    self.assertEqual(x["events_automatically_published"],0)
    self.assertEqual(x["items"][0]["state_hint"],"DF")
 def test_limits_each_source_and_does_not_set_auction_date(self):
    item={"url_kind":"candidate_direct","category_hint":"unknown"}
    x=build({"platforms":{"flex":{"candidates":[item]*25}}})
    self.assertEqual(x["candidates_count"],8)
    self.assertNotIn("auction_date",x["items"][0])
if __name__=="__main__":unittest.main()
