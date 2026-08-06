"""
Mock tests for the openclaw plugin's delegate-task-to-openclaw-agent skill.

The LLM and comm channel are mocked and deterministic, but the skill itself
runs for real: it makes an actual HTTP call to the OpenClaw Gateway - in
Docker via the local Nginx proxy (see plugins/openclaw/README.md), which is
why the container must be started with the Gateway URL known at launch (see
Autotests/mock/README.md, "5a. OpenClaw plugin"). That Gateway (mock or
live) is started and configured by the tester ahead of time - these tests do
not manage it.

Delegation is asynchronous: the skill returns an acceptance envelope at once
and the Gateway's reply is appended to history later as an OPENCLAW_RESULT
line, so the tests assert those two stages separately.

Run:
    pytest test_openclaw_delegate_mock.py -s
"""
import json
import re

from helpers import (
    Checker, dexec, make_prompt, read_history, wait_for_history_keyword,
    wait_for_skill_call, _history_block_for_run_id,
)

# The delegated task travels to a real agent and back, so allow for a slow
# Gateway; the skill call itself must still return within one iteration.
RESULT_TIMEOUT = 180
# Same shape helper.TS_RE requires to slice history into episodes.
HISTORY_BLOCK_RE = re.compile(r'\("\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"')


def _read_json(path):
    raw = dexec("cat", path).stdout.strip()
    return json.loads(raw)


def test_delegate_isolated_and_success_mock(llm, comm):
    with Checker("delegate-task-to-openclaw-agent mock") as c:
        print(f"\n=== OmegaClaw: openclaw delegate mock (run-id {c.run_id}) ===", flush=True)

        ####################################
        # Phase 1: check isolated skill call
        ####################################

        c.step("send prompt to check isolated skill invocation")
        prompt = make_prompt(c.run_id, "Delegate a task to OpenClaw.")
        llm.set_answer(
            request=prompt,
            response=(
                f'(send "Delegating task {c.run_id}")\n'
                '(delegate-task-to-openclaw-agent "Reply with exactly: unused")'
            ),
        )
        if not comm.send_message(prompt):
            c.fail("comm", "could not deliver prompt within timeout")

        c.step("verify send message does not absorb the skill")
        send_arg = wait_for_skill_call(c.run_id, "send", timeout=30, arg_substr="Delegating task")
        if not send_arg:
            c.fail("send", "Agent did not respond to first prompt.")
        if "delegate-task-to-openclaw-agent" in send_arg:
            c.fail("parser", "Bug regression: delegate call was absorbed into the send message.")
        c.ok("parser", "delegate-task-to-openclaw-agent was correctly parsed as a separate command.")

        ##############################################
        # Phase 2: acceptance envelope, then the reply
        ##############################################

        out_path = f"/tmp/openclaw_out_{c.run_id}.json"
        echo_marker = f"PONG-{c.run_id}"

        c.step("send prompt that writes the skill result straight to a file")
        prompt = make_prompt(c.run_id + 1, "Delegate a task and save the raw result.")
        llm.set_answer(
            request=prompt,
            response=(
                f'(metta (write-file "{out_path}" '
                f'(delegate-task-to-openclaw-agent "Reply with exactly: {echo_marker}")))\n'
                f'(send "Delegation saved {c.run_id}")'
            ),
        )
        if not comm.send_message(prompt):
            c.fail("comm", "could not deliver prompt within timeout")
        c.ok("comm", f"run-id={c.run_id}")

        # A short timeout on purpose: the skill hands the task to a worker
        # thread, so the acknowledging send must land without waiting for the
        # Gateway. A delegation that blocks the agent loop fails here.
        c.step("wait for the agent to acknowledge without waiting for the Gateway")
        send_arg = wait_for_skill_call(c.run_id, "send", timeout=30, arg_substr="Delegation saved")
        if not send_arg:
            c.fail("send", "Agent did not respond in time; the delegation is blocking the loop.")
        c.ok("send", "Agent stayed responsive while the delegation ran.")

        c.step("read and parse the acceptance envelope from the container")
        try:
            accepted = _read_json(out_path)
        except json.JSONDecodeError as e:
            c.fail("json", f"Failed to parse skill result: {e}")
        c.ok("json_parse", "delegate-task-to-openclaw-agent result successfully parsed")

        c.step("verify the envelope acknowledges the task")
        if accepted.get("status") != "accepted":
            c.fail("status", f"expected status 'accepted', got: {accepted}")
        if not accepted.get("id"):
            c.fail("id", f"task id missing from envelope: {accepted}")
        if echo_marker not in accepted.get("task", ""):
            c.fail("task", f"expected the task echo to mention {echo_marker!r}, got: {accepted}")
        c.ok("envelope", f"{accepted}")

        c.step("wait for the delegation result to reach history on its own")
        matched = wait_for_history_keyword(
            c.run_id,
            [f"id={accepted['id']} status=ok", echo_marker],
            timeout=RESULT_TIMEOUT,
            require_all=True,
        )
        if not matched:
            c.fail("result",
                   f"no successful OPENCLAW_RESULT for {accepted['id']} within {RESULT_TIMEOUT}s")
        c.ok("result", "the Gateway reply was appended to history")

        c.step("verify the appended record keeps history parsable by episodes")
        history = read_history()
        idx = history.find("OPENCLAW_RESULT")
        if idx == -1:
            c.fail("history", "OPENCLAW_RESULT vanished from history")
        if not HISTORY_BLOCK_RE.search(history[:idx]):
            c.fail("history", "the record is not inside a timestamped block; episodes would miss it")
        c.ok("history", "record sits in a well-formed timestamped block")

        c.done()


def test_delegate_empty_message_mock(llm, comm):
    with Checker("delegate-task-to-openclaw-agent empty message mock") as c:
        print(f"\n=== OmegaClaw: openclaw delegate empty mock (run-id {c.run_id}) ===", flush=True)

        out_path = f"/tmp/openclaw_empty_{c.run_id}.json"

        c.step("send prompt that delegates an empty message")
        prompt = make_prompt(c.run_id, "Delegate an empty task and save the raw result.")
        llm.set_answer(
            request=prompt,
            response=(
                f'(metta (write-file "{out_path}" (delegate-task-to-openclaw-agent "")))\n'
                f'(send "Empty delegation checked {c.run_id}")'
            ),
        )
        if not comm.send_message(prompt):
            c.fail("comm", "could not deliver prompt within timeout")

        c.step("wait for the agent to complete without crashing")
        send_arg = wait_for_skill_call(c.run_id, "send", timeout=30, arg_substr="Empty delegation checked")
        if not send_arg:
            c.fail("send", "Agent did not respond (might have crashed on an empty message).")
        c.ok("send", "Agent survived an empty delegation.")

        c.step("verify the skill rejected the empty message without a network call")
        try:
            result = _read_json(out_path)
        except json.JSONDecodeError as e:
            c.fail("json", f"Failed to parse skill result: {e}")
        if result.get("status") != "error" or result.get("type") != "invalid_input":
            c.fail("result", f"expected an invalid_input error, got: {result}")
        c.ok("result", f"{result}")

        c.done()


def test_delegate_new_session_per_call_mock(llm, comm):
    with Checker("delegate-task-to-openclaw-agent new session per call mock") as c:
        print(f"\n=== OmegaClaw: openclaw delegate session isolation mock (run-id {c.run_id}) ===", flush=True)

        first_path = f"/tmp/openclaw_session1_{c.run_id}.json"
        second_path = f"/tmp/openclaw_session2_{c.run_id}.json"
        first_marker = f"FIRST-{c.run_id}"
        second_marker = f"SECOND-{c.run_id}"

        c.step("send prompt that delegates two independent tasks")
        prompt = make_prompt(c.run_id, "Delegate two independent tasks and save both raw results.")
        llm.set_answer(
            request=prompt,
            response=(
                f'(metta (write-file "{first_path}" '
                f'(delegate-task-to-openclaw-agent "Reply with exactly: {first_marker}")))\n'
                f'(metta (write-file "{second_path}" '
                f'(delegate-task-to-openclaw-agent "Reply with exactly: {second_marker}")))\n'
                f'(send "Both delegations saved {c.run_id}")'
            ),
        )
        if not comm.send_message(prompt):
            c.fail("comm", "could not deliver prompt within timeout")

        c.step("wait for the agent to acknowledge both delegations")
        send_arg = wait_for_skill_call(c.run_id, "send", timeout=30, arg_substr="Both delegations saved")
        if not send_arg:
            c.fail("send", "Agent did not respond in time; a delegation is blocking the loop.")
        c.ok("send", "Agent accepted both delegations.")

        c.step("verify each delegation got its own task id")
        try:
            first = _read_json(first_path)
            second = _read_json(second_path)
        except json.JSONDecodeError as e:
            c.fail("json", f"Failed to parse a skill result: {e}")
        if first.get("status") != "accepted" or second.get("status") != "accepted":
            c.fail("status", f"expected both to be accepted, got: {first}, {second}")
        if not first.get("id") or first.get("id") == second.get("id"):
            c.fail("id", f"task ids must differ, got: {first.get('id')} and {second.get('id')}")
        c.ok("ids", f"{first['id']} and {second['id']}")

        c.step("wait for both replies to reach history")
        matched = wait_for_history_keyword(
            c.run_id,
            [f"id={first['id']} status=ok", f"id={second['id']} status=ok"],
            timeout=RESULT_TIMEOUT,
            require_all=True,
        )
        if not matched:
            c.fail("result",
                   f"both successful OPENCLAW_RESULT records did not arrive within {RESULT_TIMEOUT}s")
        c.ok("result", "both replies were appended to history")

        # Scoped to this run's slice of history so ids left by earlier tests
        # cannot make the comparison pass on their own.
        c.step("verify the two calls ran in separate Gateway sessions")
        window = _history_block_for_run_id(read_history(), c.run_id) or ""
        response_ids = set(re.findall(r"responseId=(\S+)", window))
        if len(response_ids) < 2:
            c.fail("session isolation",
                   f"expected two distinct responseId values, found: {response_ids or 'none'}")
        c.ok("session isolation", f"{len(response_ids)} distinct responseId values")

        c.done()
