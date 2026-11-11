import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # run tests without installing

from handmade.brief import Facts, detect_domain, extract, interview, is_vague, photo_choice, plan
from handmade.prompt import Brief, build_prompt, detect_intent


def scripted(answers):
    # An ask() that replays answers in order, then presses Enter.
    queue = list(answers)
    return lambda _prompt: queue.pop(0) if queue else ""


class ExtractTests(unittest.TestCase):
    def test_product_and_place_come_from_the_request(self):
        facts = extract("build a landing page for my bakery shop in Nairobi")
        self.assertEqual(facts.get("product"), "bakery shop")
        self.assertEqual(facts.get("place"), "Nairobi")

    def test_no_product_is_invented(self):
        self.assertNotIn("product", extract("make it look nice"))

    def test_product_regex_keeps_whole_words(self):
        facts = extract("a dashboard for African fintechs, please")
        self.assertEqual(facts.get("product"), "African fintechs")


class DomainTests(unittest.TestCase):
    def test_known_domains(self):
        self.assertEqual(detect_domain("landing page for my bakery").name, "food")
        self.assertEqual(detect_domain("clinic records dashboard").name, "health")
        self.assertEqual(detect_domain("sacco signup form").name, "finance")

    def test_the_trade_beats_the_word_shop(self):
        self.assertEqual(detect_domain("booking page for a barber shop").name, "hospitality")
        self.assertEqual(detect_domain("a phone shop").name, "retail")

    def test_unknown_domain_falls_back(self):
        self.assertEqual(detect_domain("a page about nothing in particular").name, "general")


class VagueTests(unittest.TestCase):
    def test_vague_answers(self):
        for answer in ("everyone", "anyone", "users", "amazing", "modern and clean", "idk", "nice"):
            self.assertTrue(is_vague(answer), answer)

    def test_specific_answers(self):
        for answer in ("university students on their phones", "order a cake on WhatsApp", "the Kenya Gazette"):
            self.assertFalse(is_vague(answer), answer)


class InterviewTests(unittest.TestCase):
    def run_interview(self, answers, request="build a landing page for my bakery shop in Nairobi"):
        facts = Facts()
        facts.values.update(extract(request))
        intent = detect_intent(request, facts.get("product"))
        return interview(request, facts, intent, "warm", scripted(answers), lambda _m: None), intent

    def test_questions_follow_the_domain(self):
        facts = Facts()
        facts.values.update(extract("landing page for my bakery shop"))
        keys = [q.key for q in plan("landing page for my bakery shop", facts, "landing", "warm")]
        self.assertIn("audience", keys)
        self.assertIn("goal", keys)
        self.assertNotIn("product", keys)  # already known from the request

    def test_vague_answer_gets_one_follow_up_then_is_marked(self):
        facts, _ = self.run_interview(["everyone", "anyone"])
        self.assertNotIn("audience", facts.values)
        self.assertEqual(facts.vague.get("audience"), "anyone")

    def test_follow_up_can_rescue_a_vague_answer(self):
        facts, _ = self.run_interview(["everyone", "university students on their phones"])
        self.assertEqual(facts.get("audience"), "university students on their phones")

    def test_vague_optional_answer_is_not_accepted(self):
        facts = Facts()
        facts.values.update({"product": "bakery shop", "audience": "students", "goal": "order on WhatsApp"})
        keys = [q.key for q in plan("landing page for my bakery shop", facts, "landing", "warm")]
        answers = ["" if k != "reference" else "amazing" for k in keys]
        result = interview("landing page for my bakery shop", facts, "landing", "warm", scripted(answers), lambda _m: None)
        self.assertNotIn("reference", result.values)
        self.assertEqual(result.vague.get("reference"), "amazing")

    def test_enter_on_mood_accepts_the_suggestion(self):
        facts, _ = self.run_interview([])
        self.assertEqual(facts.get("mood"), "warm")

    def test_empty_answers_stay_missing(self):
        facts, _ = self.run_interview([])
        self.assertNotIn("audience", facts.values)
        self.assertNotIn("goal", facts.values)


class PhotoTests(unittest.TestCase):
    def test_reading_the_photo_answer(self):
        cases = {
            "stock photos are fine for now": "stock", "use unsplash": "stock", "yes": "stock",
            "we have photos of the shop": "own", "our own": "own",
            "we don't have any photos yet": "none", "no": "none", "none yet": "none",
            "we don't have any, stock is fine": "stock", "hmm": "",
        }
        for answer, expected in cases.items():
            self.assertEqual(photo_choice(answer), expected, answer)

    def test_photos_are_asked_only_where_pages_show_photos(self):
        facts = Facts()
        facts.values["product"] = "barber shop"
        self.assertIn("photos", [q.key for q in plan("landing page for my barber shop", facts, "landing", "warm")])
        self.assertNotIn("photos", [q.key for q in plan("clinic dashboard", facts, "dashboard", "civic")])

    def test_interview_stores_the_choice(self):
        facts = Facts()
        facts.values.update({"product": "barber shop", "audience": "office workers", "goal": "book a cut"})
        keys = [q.key for q in plan("landing page for my barber shop", facts, "landing", "warm")]
        answers = ["stock is fine" if k == "photos" else "" for k in keys]
        result = interview("landing page for my barber shop", facts, "landing", "warm", scripted(answers), lambda _m: None)
        self.assertEqual(result.get("photos"), "stock")

    def test_images_section_follows_the_answer(self):
        base = dict(request="landing page for my barber shop", product="barber shop", audience="office workers")
        stock, _ = build_prompt(Brief(**base, answers={"photos": "stock", "place": "Nairobi"}))
        self.assertIn("agreed to free stock photos", stock)
        self.assertIn("barber shop in Nairobi", stock)
        unknown, _ = build_prompt(Brief(**base))
        self.assertIn("Do not hotlink stock photos", unknown)
        dashboard, _ = build_prompt(Brief(request="clinic dashboard", product="clinic records", intent="dashboard"))
        self.assertNotIn("## Images", dashboard)


class PromptFactsTests(unittest.TestCase):
    def test_explicit_page_beats_domain_words(self):
        self.assertEqual(detect_intent("build a landing page for my bakery shop"), "landing")
        self.assertEqual(detect_intent("admin dashboard for an online shop"), "dashboard")
        self.assertEqual(detect_intent("booking page for a barber shop", "barber shop"), "landing")

    def test_missing_facts_are_listed_not_invented(self):
        text, _ = build_prompt(Brief(request="landing page for my bakery shop", product="bakery shop"))
        self.assertIn("Facts still missing", text)
        self.assertIn("do not invent", text)

    def test_vague_facts_are_listed_as_missing(self):
        text, _ = build_prompt(Brief(request="landing page", product="bakery", vague={"audience": "everyone"}))
        self.assertIn("everyone", text.split("Facts still missing", 1)[1])

    def test_saved_system_is_reused(self):
        first, system = build_prompt(Brief(request="landing page", product="bakery", mood="warm"))
        again, same = build_prompt(Brief(request="pricing page", product="bakery"), saved_system=system.to_dict())
        self.assertEqual(system.colors, same.colors)
        self.assertEqual(system.display_font, same.display_font)


if __name__ == "__main__":
    unittest.main()
