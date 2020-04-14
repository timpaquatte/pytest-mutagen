from mutagen import *
from _pytest.reports import TestReport
from _pytest.runner import runtestprotocol
from _pytest.config import ExitCode
import sys

import pytest

MUTAGEN_OPTION = "--mutate"

all_test_passed = True
failed_mutants = []

def pytest_addoption(parser):
    group = parser.getgroup("mutagen", "Mutagen")
    group.addoption(
        MUTAGEN_OPTION,
        action="store_true",
        help="activate the mutation testing tool",
    )

def pytest_report_header(config):
    if config.getoption(MUTAGEN_OPTION):
        return 'hypothesis-mutagen-1.0.0 : Mutations enabled'

def pytest_report_teststatus(report, config):
    global all_test_passed
    if report.when == "call":
        if report.outcome == "mutpassed":
            return "mut_passed", "m", ("MUT", {"purple": True})
        elif report.outcome == "mutfailed":
            all_test_passed = False
            return "mut_failed", "M", ("MUTF", {"red": True})


def pytest_runtest_makereport(item, call):
    report = TestReport.from_item_and_call(item, call)
    if g_current_mutant and report.when == "call":
        report.outcome = "mut" + report.outcome
    return report

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    global g_mutant_registry
    global g_current_mutant
    global all_test_passed
    global failed_mutants

    if not session.config.getoption(MUTAGEN_OPTION):
        return

    print("\nRunning mutations :")

    session.exitstatus = ExitCode.TESTS_FAILED
    session.testsfailed = 1

    for mutant in g_mutant_registry.values():
        print(mutant.name)
        g_current_mutant = mutant
        all_test_passed = True

        def f():
            for module in session.collect():
                for x in module.collect():
                    runtestprotocol(x)

        mutant.apply_and_run(f)
        g_current_mutant = None
        if all_test_passed:
            print("\t/!\ ALL TESTS PASSED")
            failed_mutants.append(mutant.name)
            session.exitstatus = ExitCode.TESTS_FAILED
            exitstatus = ExitCode.TESTS_FAILED
        print()

    print("Done")

def pytest_terminal_summary(terminalreporter):
        terminalreporter.section("Mutagen")

        if failed_mutants != []:
            print("The following mutants passed all tests:")
        for mutant in failed_mutants:
            print(mutant)