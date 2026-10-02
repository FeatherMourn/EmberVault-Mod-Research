import tempfile
import unittest
from pathlib import Path
from community_service import CommunityService


class CommunityServiceTests(unittest.TestCase):
    def test_submission_requires_moderator_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            service = CommunityService(Path(temp))
            member = service.create_user("Member")
            moderator = service.create_user("Moderator", ["moderator"])
            submission = service.submit(member["id"], "mod", "A public mod")
            self.assertEqual(submission["status"], "submitted")
            approved = service.review(moderator["id"], submission["id"], "approve", "Reviewed public metadata")
            self.assertEqual(approved["status"], "approved")
            with self.assertRaises(ValueError):
                service.publish_submission(member["id"], submission["id"])
            published = service.publish_submission(moderator["id"], submission["id"])
            self.assertEqual(published["status"], "published")

    def test_suspended_user_cannot_submit_or_post(self):
        with tempfile.TemporaryDirectory() as temp:
            service = CommunityService(Path(temp)); user = service.create_user("Suspended")
            data = service._load(); data["users"][0]["status"] = "suspended"; service._save(data)
            with self.assertRaises(ValueError):
                service.submit(user["id"], "research", "Hidden")

    def test_moderation_is_role_checked_and_audited(self):
        with tempfile.TemporaryDirectory() as temp:
            service = CommunityService(Path(temp)); moderator = service.create_user("Moderator", ["moderator"]); member = service.create_user("Member")
            thread = service.create_thread(member["id"], "Build notes", "A public note")
            action = service.moderate(moderator["id"], thread["id"], "lock", "Freeze the thread for review")
            self.assertEqual(action["action"], "lock")
            with self.assertRaises(ValueError):
                service.moderate(member["id"], thread["id"], "restore", "Not authorized")

    def test_forum_replies_and_projects_obey_publication_boundaries(self):
        with tempfile.TemporaryDirectory() as temp:
            service = CommunityService(Path(temp)); user = service.create_user("Creator", ["creator"])
            thread = service.create_thread(user["id"], "Build notes", "Opening post")
            post = service.reply_thread(user["id"], thread["id"], "Follow-up evidence")
            self.assertEqual(post["body"], "Follow-up evidence")
            private = service.create_project(user["id"], "Private work", "private", ["EV-RES-1"])
            public = service.create_project(user["id"], "Public work", "public", ["EV-KNOW-1"])
            self.assertEqual(private["status"], "draft")
            self.assertEqual(public["status"], "review")
            service.moderate(service.create_user("Mod", ["moderator"])["id"], thread["id"], "lock", "Archive discussion")
            with self.assertRaises(ValueError):
                service.reply_thread(user["id"], thread["id"], "Blocked reply")


if __name__ == "__main__":
    unittest.main()
