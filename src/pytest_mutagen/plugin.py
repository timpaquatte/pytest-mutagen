import pytest_mutagen.mutagen as mg
from _pytest.reports import TestReport
from _pytest.runner import runtestprotocol
from _pytest.config import ExitCode
from _pytest.terminal import TerminalReporter
from os import path

import pytest

MUTAGEN_OPTION = "--mutate"
QUICK_MUTATIONS = "--quick-mut"

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

def pytest_report_header(config):
    return 'pytest-mutagen-1.0 : Mutations ' + ('enabled' if config.getoption(MUTAGEN_OPTION) else 'disabled')

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

def check_cache_and_rearrange(module_name, session, mutant_name, collection):
    cached_failures = session.config.cache.get("mutagen/" + module_name + "/" + mutant_name, None)
    expected_failures = []
    expected_successes = []
    if not cached_failures is None:
        for item in collection:
            if get_func_from_item(item).__qualname__ in cached_failures:
                expected_failures.append(item)
            else:
                expected_successes.append(item)
        session.config.cache.set("mutagen/" + module_name + "/" + mutant_name, [])
        return expected_failures + expected_successes
    return collection

def write_in_cache(module_name, session, item, mutant_name):
    l = session.config.cache.get("mutagen/" + module_name + "/" + mutant_name, None)
    new_val = get_func_from_item(item).__qualname__
    session.config.cache.set("mutagen/" + module_name + "/" + mutant_name, ([] if l is None else l) + [new_val])

def remove_classes(l):
    from _pytest.python import Class, Instance

    i = 0
    while i < len(l):
        if isinstance(l[i], Class) or isinstance(l[i], Instance):
            del l[i]
        else:
            i += 1

def get_stacked_collection(session):
    items = session.items

    # Syntax from by _pytest.terminal.TerminalReporter._printcollecteditems
    stack = []
    collected = []
    collectors = []
    function_list = []
    for item in items:
        needed_collectors = item.listchain()[1:]  # strip root node
        remove_classes(needed_collectors)
        while stack:
            if stack == needed_collectors[: len(stack)]:
                break
            stack.pop()
        if len(stack) == len(needed_collectors) - 1:
            function_list.append(needed_collectors[-1])
        else:
            collected.append(collectors + [function_list])
            collectors = []
            for col in needed_collectors[len(stack) :]:
                stack.append(col)
                collectors.append(col)
            function_list = [collectors.pop()]
    collected.append(collectors + [function_list])
    collected.pop(0)
    return collected

def get_mutants_per_module(module_name):
    mutants = list(mg.g_mutant_registry[mg.APPLY_TO_ALL].values())

    if module_name in mg.g_mutant_registry:
        mutants += list(mg.g_mutant_registry[module_name].values())

    return mutants

def display_item(reporter, item):
    from _pytest.python import Module, Package

    reporter._tw.line()
    if isinstance(item, Package):
        reporter.write_sep("-", "Package " + path.basename(item.name) + ":", bold=False)
    elif isinstance(item, Module):
        reporter.write_line("Module " + path.basename(item.name) + ":")
    else:
        reporter.write_line("Not recognized " + ":")

def parse_stacked(session, stacked, carry):
    global mutants_passed_all_tests

    basename = path.basename(stacked[-2].name) if len(stacked) > 1 else ""
    collection = stacked[-1]
    mutants = get_mutants_per_module(basename)
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")

    for k in range(min(len(carry), len(stacked) - 1)):
        carry.pop()
    carry.extend(stacked)
    carry.pop()

    specified_in_args = basename in [path.basename(a) for a in session.config.args]
    if len(mutants) > 0 or specified_in_args:
        mutants_passed_all_tests[basename] = []
        for item in carry:
            display_item(reporter, item)
        carry = []

    if len(mutants) == 0 and specified_in_args:
        reporter.write_line("No mutant registered", **{"purple": True})

    return basename, collection, mutants

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    global mutants_passed_all_tests

    if not session.config.getoption(MUTAGEN_OPTION):
        return

    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    reporter._tw.line()
    reporter.write_sep("=", "mutation session starts", bold=True)
    reporter.showfspath = False

    if len(reporter.getreports("error")) > 0 or len(reporter.getreports("failed")) > 0:
        return

    collected = get_stacked_collection(session)
    carry = []

    for stacked in collected:
        basename, collection, mutants = parse_stacked(session, stacked, carry)

        for mutant in mutants:
            collection = check_cache_and_rearrange(basename, session, mutant.name, collection)

            mg.g_current_mutant = mutant
            all_test_passed = True
            skip = False
            for item in collection:
                if not skip:
                    saved_globals = modify_environment(item, mutant)
                    reports = runtestprotocol(item)
                    if any(("failed" in report.outcome) for report in reports):
                        write_in_cache(basename, session, item, mutant.name)
                        all_test_passed = False
                        if session.config.getoption(QUICK_MUTATIONS):
                            skip = True
                    restore_environment(item, mutant, saved_globals)
                else:
                    reporter.write(" ")

            mg.g_current_mutant = None

            if all_test_passed:
                reporter.write_line("\t" + mutant.name + "\t/!\ ALL TESTS PASSED")
                mutants_passed_all_tests[basename].append(mutant.name)
                session.exitstatus = ExitCode.TESTS_FAILED
            else:
                reporter.write_line("\t" + mutant.name)

    reporter.stats["error"] = []
    reporter.stats["failed"] = []

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

def get_func_from_item(item):
    if not hasattr(item, "function"):
        return None
    if hasattr(item.function, "is_hypothesis_test") and getattr(item.function, "is_hypothesis_test"):
        return getattr(item.function, "hypothesis").inner_test
    return item.function

def get_object_to_modify(obj_name, f, repl):
    obj_to_modify = None
    if obj_name in f.__globals__:
        obj_to_modify = f.__globals__[obj_name]
    elif obj_name in repl.__globals__:
        obj_to_modify = repl.__globals__[obj_name]

    if obj_to_modify is None:
        raise NameError("Could not find " + obj_name + ", make sure that it's imported in the file containing mutations")
    return obj_to_modify

def modify_environment(item, mutant):
    saved = {}
    f = get_func_from_item(item)

    if f is None:
        return []

    for func_name, repl in mutant.function_mappings.items():
        if not "." in func_name:
            func_to_modify = get_object_to_modify(func_name, f, repl)

            saved[func_name] = func_to_modify.__globals__[func_name].__code__
            func_to_modify.__globals__[func_name].__code__ = repl.__code__
        else:
            l = func_name.split(".", 1)
            class_to_modify = get_object_to_modify(l[0], f, repl)

            saved[func_name] = class_to_modify.__dict__[l[1]]

            if isinstance(saved[func_name], staticmethod):
                setattr(class_to_modify, l[1], staticmethod(repl))
            elif isinstance(saved[func_name], property):
                new_prop = property(fget=repl, fset=saved[func_name].fset, fdel=saved[func_name].fdel)
                setattr(class_to_modify, l[1], new_prop)
            else:
                setattr(class_to_modify, l[1], repl)

    return saved

def restore_environment(item, mutant, saved):
    f = get_func_from_item(item)

    for func_name in saved:
        if not "." in func_name:
            func_to_modify = get_object_to_modify(func_name, f, mutant.function_mappings[func_name])
            func_to_modify.__globals__[func_name].__code__ = saved[func_name]
        else:
            l = func_name.split(".", 1)
            class_to_modify = get_object_to_modify(l[0], f, mutant.function_mappings[func_name])
            setattr(class_to_modify, l[1], saved[func_name])