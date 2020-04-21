from mutagen import *
from _pytest.reports import TestReport
from _pytest.runner import runtestprotocol
from _pytest.config import ExitCode
from _pytest.terminal import TerminalReporter
import sys

import pytest

MUTAGEN_OPTION = "--mutate"
QUICK_MUTATIONS = "--quick-mut"

all_test_passed = True
failed_mutants = {}

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

def pytest_report_header(config):
    return 'hypothesis-mutagen-1.0.0 : Mutations ' + ('enabled' if config.getoption(MUTAGEN_OPTION) else 'disabled')

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

    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    reporter._tw.line()
    reporter.write_sep("=", "mutation session starts", bold=True)
    reporter.showfspath = False

    for module in session.collect():
        basename = path.basename(module.name)
        collection = module.collect()

        if type(collection) != type([]):
            continue

        failed_mutants[basename] = []
        reporter._tw.line()
        reporter.write_line("Module " + basename + ":")

        for mutant in filter(lambda x: x.file == basename, g_mutant_registry.values()):
            g_current_mutant = mutant
            all_test_passed = True


            def f():
                skip = False
                for item in collection:
                    if not skip:
                        saved_globals = modify_environment(item, mutant)
                        reports = runtestprotocol(item)
                        if session.config.getoption(QUICK_MUTATIONS):
                            for report in filter(lambda x: x.outcome == "mutfailed", reports):
                                skip = True
                        restore_environment(item, mutant, saved_globals)
                    else:
                        reporter.write(" ")

            mutant.apply_and_run(f)
            g_current_mutant = None

            if all_test_passed:
                reporter.write_line("\t" + mutant.name + "\t/!\ ALL TESTS PASSED")
                failed_mutants[basename].append(mutant.name)
                session.exitstatus = ExitCode.TESTS_FAILED
            else:
                reporter.write_line("\t" + mutant.name)

def pytest_terminal_summary(terminalreporter):
    terminalreporter.section("Mutagen")

    for module in failed_mutants:
        if failed_mutants[module] != []:
            terminalreporter.write("[ERROR]   ", **{"red": True})
            terminalreporter.write_line(module + ": The following mutants passed all tests: " + str(failed_mutants[module]))
        else:
            terminalreporter.write("[SUCCESS] ", **{"green": True})
            terminalreporter.write_line(module + ": All mutants made at least one test fail")

def modify_environment(item, mutant):
    saved = {}

    for func, repl in mutant.function_mappings.items():
        if not "." in func:
            if func in item.function.__globals__:
                saved[func] = item.function.__globals__[func]
            item.function.__globals__[func] = repl
        else:
            l = func.split(".", 1)
            if l[0] in item.function.__globals__:
                saved[func] = getattr(item.function.__globals__[l[0]], l[1])
                setattr(item.function.__globals__[l[0]], l[1], repl)
            else:
                print(l[0], " is not in the globals of ", item.function)

    return saved

def restore_environment(item, mutant, saved):
    for func in saved:
        if not "." in func:
            if func in item.function.__globals__:
                item.function.__globals__[func] = saved[func]
        else:
            l = func.split(".", 1)
            if l[0] in item.function.__globals__:
                setattr(item.function.__globals__[l[0]], l[1], saved[func])