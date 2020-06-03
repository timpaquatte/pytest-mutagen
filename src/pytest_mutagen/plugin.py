import os
import sys

import pytest
from _pytest.reports import TestReport
from _pytest.nodes import File

import pytest_mutagen.mutagen as mg
from pytest_mutagen.mutation_session import MutationSession


MUTAGEN_OPTION = "--mutate"
QUICK_MUTATIONS = "--quick-mut"
SELECT_MUTANTS = "--select"
MUTAGEN_STATS = "--mutagen-stats"

mutants_passed_all_tests = {}

def pytest_addoption(parser):
    group = parser.getgroup("mutagen", "Mutagen")
    group.addoption(
        MUTAGEN_OPTION,
        action="store_true",
        help="activate the mutation testing tool",
    )
    group.addoption(
        QUICK_MUTATIONS,
        action="store_true",
        help="each mutant stops after the first failed test"
    )
    group.addoption(
        SELECT_MUTANTS,
        action="store",
        type="string",
        dest="MUTANTS",
        help="select the mutants to run (comma-separated for several values)"
    )
    group.addoption(
        MUTAGEN_STATS,
        action="store_true",
        help="show the number of tests that caught each mutant"
    )

def pytest_collect_file(parent, path):
    if parent.config.getoption(MUTAGEN_OPTION):
        if path.ext == ".py" and "mutations" in path.basename:
            ihook = parent.session.gethookproxy(path)
            return ihook.pytest_pycollect_makemodule(path=path, parent=parent)

def pytest_report_header(config):
    from ._version import __version__
    return 'pytest-mutagen-' + __version__ + ' : Mutations ' + ('enabled' if config.getoption(MUTAGEN_OPTION) else 'disabled')

def pytest_report_teststatus(report, config):
    if report.outcome == "mutpassed":
        return "mut_passed", "m", ("MUT", {"purple": True})
    elif report.outcome == "mutfailed":
        return "mut_failed", "M", ("MUTF", {"red": True})

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    report = TestReport.from_item_and_call(item, call)
    if (not mg.g_current_mutant is None) and report.when == "call" and report.outcome in ["failed", "passed"]:
        report.outcome = "mut" + report.outcome
    return report


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):

    if not session.config.getoption(MUTAGEN_OPTION):
        return

    mutation_session = MutationSession(session)
    mutation_session.run_session()

def pytest_terminal_summary(terminalreporter):
    global mutants_passed_all_tests

    if not terminalreporter.config.getoption(MUTAGEN_OPTION):
        return

    if len(terminalreporter.getreports("error")) > 0 or len(terminalreporter.getreports("failed")) > 0:
        terminalreporter.write_line("Mutants were not run because the test suite failed", **{"red": True})
        return

    terminalreporter.section("Mutagen")

    for module, mutants in mg.g_mutant_registry.items():
        passed_all = mutants_passed_all_tests.get(module, [])
        name = module

        if module == mg.APPLY_TO_ALL:
            if len(mutants) == 0:
                continue
            passed_all = set(mutants)
            for v in mutants_passed_all_tests.values():
                passed_all &= set(v)
            passed_all = list(passed_all)
            name = "Global"

        if passed_all != []:
            terminalreporter.write("[ERROR]   ", **{"red": True})
            terminalreporter.write_line(name + ": The following mutants passed all tests: " + str(passed_all))
        else:
            terminalreporter.write("[SUCCESS] ", **{"green": True})
            terminalreporter.write_line(name + ": All mutants made at least one test fail")

    if terminalreporter.config.getoption(MUTAGEN_STATS):
        terminalreporter.write_line("")
        terminalreporter.write_line("Number of catches per mutants :", cyan=True)
        for module, mutants in mg.g_mutant_registry.items():
            for name, mutant in sorted(mutants.items(), key=lambda x: x[1].nb_catches):
                terminalreporter.write_line(str(mutant.nb_catches) + " : " + name)
