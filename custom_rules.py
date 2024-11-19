import re
from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleSeverity
from collections import Counter

rules = {
    "MK1000": Rule(rule_id="MK1000", name="tags-not-match", msg="Tags in Test name {{test_name_tags}} is not equal to Tags {{tags}}", severity=RuleSeverity.WARNING),
    "MK1001": Rule(rule_id="MK1001", name="tags-not-found-on-test-name", msg="Test name must contain at least one tag e.g. MAKNET-xxxx ", severity=RuleSeverity.WARNING),
    "MK1002": Rule(rule_id="MK1002", name="tags-not-found-tags", msg="Tags must contain at least one tag e.g. MAKNET-xxxx ", severity=RuleSeverity.WARNING),
    "MK1003": Rule(rule_id="MK1003", name="tags-must-have-priority", msg="Tags must contain at least one priority e.g. priority-xxxx ", severity=RuleSeverity.WARNING),
    "MK1004": Rule(rule_id="MK1004", name="tags-common", msg="Tags must contain at least one of {{common_tags}}", severity=RuleSeverity.WARNING),
    "MK1005": Rule(rule_id="MK1005", name="testname-special-character", msg="Test name not allow to use Double quotes and Slash.", severity=RuleSeverity.WARNING),
    "MK1006": Rule(rule_id="MK1006", name="wait-page-load-in-test", msg="Not allow to use wait page load in testcase. Please do in keywords.", severity=RuleSeverity.WARNING),
    "MK1007": Rule(rule_id="MK1007", name="no-run-keyword-if", msg="Not allow to use Run keyword if.", severity=RuleSeverity.WARNING),
    "MK1008": Rule(rule_id="MK1008", name="platform-tags", msg="Test from {{path}} must contain platform tags {{platform_tags}}", severity=RuleSeverity.WARNING),
    "MK1009": Rule(rule_id="MK1009", name="builtin_library", msg="Not allow to use builtin for prefix", severity=RuleSeverity.WARNING),
    "MK1010": Rule(rule_id="MK1010", name="debug_library", msg="Not allow to use debuglibrary", severity=RuleSeverity.WARNING)
}

class NoExamplesChecker(VisitorChecker):
    reports = ("tags-not-match",
               "tags-not-found-on-test-name",
               "tags-not-found-tags",
               "tags-must-have-priority",
               "tags-common",
               "testname-special-character",
               "wait-page-load-in-test",
               "no-run-keyword-if",
               "platform-tags",
               "builtin_library",
               "debug_library",
               )
    
    def visit_File(self, node):
        self.path = str(node.source)
        if "/tests/mobile" in self.path:
            self.platform_tags = ["android", "ios"]
        elif "/tests/web" in self.path:
            self.platform_tags = ["web"]
        elif "/tests/backend/api" in self.path:
            self.platform_tags = ["api"]
        self.generic_visit(node)

    def visit_TestCaseName(self, node):
        self.test_name_tags = re.findall("MAKNET-[\d]+", node.name)
        if not self.test_name_tags:
            self.report("tags-not-found-on-test-name", node=node, lineno=node.lineno)
        matches_special_character = re.findall('["/]', node.name)
        if matches_special_character:
            self.report("testname-special-character", node=node, lineno=node.lineno)
    
    def visit_Tags(self, node):
        self.tags = list(filter(lambda x: re.search("MAKNET-[\d]+", x), node.values))
        if not self.tags:
            self.report("tags-not-found-tags", node=node, lineno=node.lineno)
        self.check_tags(node)
        self.check_priority(node)
        self.check_tags_common(node)
        self.check_platform_tags(node)
        
    def visit_KeywordCall(self, node):
        if  node.keyword.lower().replace(" ", "").replace("_", "") in {"mobilecommon.waituntilloadingcomplete", "webcommon.waitforpageload"} and "/tests/" in self.path:
            self.report("wait-page-load-in-test", node=node, lineno=node.lineno)
        if "runkeywordif" == node.keyword.lower().replace("builtin.", "").replace(" ", "").replace("_", ""):
            self.report("no-run-keyword-if", node=node, lineno=node.lineno)
        if node.keyword.lower().startswith("builtin."):
            self.report("builtin_library", node=node, lineno=node.lineno)
            
    def visit_LibraryImport(self, node):  # noqa
        if not node.name:
            return
        if node.name.lower() == "debuglibrary":
            self.report("debug_library", node=node)
    
    def check_tags(self, node):
        if Counter(self.test_name_tags) != Counter(self.tags):
            self.report("tags-not-match", node=node, test_name_tags=self.test_name_tags, tags=self.tags)

    def check_priority(self, node):
        priority = list(filter(lambda x: re.search("priority_[a-z]+", x), node.values))
        if not priority:
            self.report("tags-must-have-priority", node=node)
        
    def check_tags_common(self, node):
        common = ["sanity", "regression", "smoke", "must_pass", "extra-coverage"]
        intersection = list(set(node.values) & set(common))
        if not intersection:
            self.report("tags-common", node=node, common_tags=common)
    
    def check_platform_tags(self, node):
        intersection = list(set(node.values) & set(self.platform_tags))
        if not intersection:
            self.report("platform-tags", node=node, path=self.path, platform_tags=self.platform_tags)
            