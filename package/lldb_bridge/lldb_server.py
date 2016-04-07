#!/usr/bin/python
from __future__ import print_function
from SimpleXMLRPCServer import SimpleXMLRPCServer

import sys
import threading

if len(sys.argv) < 2:
    print("Usage: {} <lldb_python_path> [port]".format(sys.argv[0]))
    lldb_path = '/Library/Developer/Toolchains/swift-latest.xctoolchain/System/Library/PrivateFrameworks/LLDB.framework/Resources/Python'
    port = 12597
#    sys.exit(1)
elif len(sys.argv) == 2:
    lldb_path = sys.argv[1]
    port = 12597
elif len(sys.argv) == 3:
    lldb_path = sys.argv[1]
    port = int(sys.argv[2])    

print("Running with Python module path {} on localhost:{}...".format(lldb_path, port))
sys.path.insert(1, lldb_path)
from lldb import *

server = None
target = None
process = None
stop_event_listener = None
out_event_listener = None
stdout_buffer = ""
stderr_buffer = ""
status = "unknown"
breakpoint_status = {}

lldb_handle = SBDebugger.Create()
lldb_handle.SetAsync(True)

# Internal
def _stop_event():
    global status
    event = SBEvent()
    broadcaster = process.GetBroadcaster()
    while True:
        if not stop_event_listener:
            return
        if stop_event_listener.WaitForEventForBroadcasterWithType(1, broadcaster, SBProcess.eBroadcastBitStateChanged, event):
            state = process.GetState()
            if state == eStateLaunching:
                status = "launching"
            elif state == eStateRunning:
                status = "running"
            elif state == eStateStopped:
                s = ["stopped"]

                breakpoint = watchpoint = signal = exception = False
                for thread in process.threads:
                    reason = thread.GetStopReason()
                    if reason == eStopReasonBreakpoint:
                        breakpoint = True
                    elif reason == eStopReasonWatchpoint:
                        watchpoint = True
                    elif reason == eStopReasonSignal:
                        signal = True
                    elif reason == eStopReasonException:
                        exception = True
                
                if breakpoint:
                    s.append('breakpoint')
                if watchpoint:
                    s.append('watchpoint')
                if signal:
                    s.append('signal')
                if exception:
                    s.append('exception')

                status = ",".join(s)
            elif state == eStateStepping:
                status = "stepping"
            elif state == eStateCrashed:
                status = "crashed"
            elif state == eStateExited:
                status = "exited"
            else:
                status = "unknown"

def _output_event():
    global stderr_buffer, stdout_buffer
    event = SBEvent()
    broadcaster = process.GetBroadcaster()
    while True:
        if not out_event_listener:
            return
        if out_event_listener.WaitForEventForBroadcasterWithType(1, broadcaster, SBProcess.eBroadcastBitSTDOUT | SBProcess.eBroadcastBitSTDERR, event):
            if event.GetType() == 4:
                result = process.GetSTDOUT(1024)
                if result:
                    stdout_buffer += result
            else:
                stream = SBStream()
                event.GetDescription(stream)
                print("output event", stream.GetData())
                print("stderr", process.GetSTDERR(1024))

def shutdown_server():
    global server, out_event_listener, stop_event_listener
    stop()
    out_event_listener = None
    stop_event_listener = None
    SBDebugger.Destroy(lldb_handle)
    server.server_close()

# load executable
def prepare(executable, params, environment, path, work_dir):
    global target, process, stop_event_listener, out_event_listener
    if not target:
        target = lldb_handle.CreateTargetWithFileAndTargetTriple(executable, LLDB_ARCH_DEFAULT)
    if not target:
        raise Exception("Could not create target")       

    error = SBError()
    process = target.Launch(lldb_handle.GetListener(), params, environment, None, None, None, work_dir, 0, True, error)
    if not error.Success():
        raise Exception("Could not load target: " + str(error))

    stop_event_listener = SBListener('stop_listener')
    out_event_listener = SBListener('output_listener')
    
    broadcaster = process.GetBroadcaster()
    if not broadcaster.AddListener(stop_event_listener, SBProcess.eBroadcastBitStateChanged):
        raise Exception("Could not add stop listener")

    if not broadcaster.AddListener(out_event_listener, SBProcess.eBroadcastBitSTDOUT | SBProcess.eBroadcastBitSTDERR):
        raise Exception("Could not add out listener")

    threading.Thread(target=_stop_event, name='stop_event_listener', args=()).start()
    threading.Thread(target=_output_event, name='output_event_listener', args=()).start()

# running, interrupting and stepping
def start():
    global process
    if not process:
        raise Exception("No process to run")
    error = process.Continue()
    if not error.Success():
        raise Exception("Could not continue: " + str(error))

def pause():
    global process
    if not process:
        raise Exception("No process to pause")
    error = process.Stop()
    if not error.Success():
        raise Exception("Could not continue: " + str(error))

def step_into():
    global process
    if not process:
        raise Exception("No process to step")
    thread = process.GetSelectedThread()
    thread.StepInto()

def step_over():
    global process
    if not process:
        raise Exception("No process to step")
    thread = process.GetSelectedThread()
    thread.StepOver()

def step_out():
    global process
    if not process:
        raise Exception("No process to step")
    thread = process.GetSelectedThread()
    thread.StepOut()

def stop():
    global process, stop_event_listener
    if process:
        error = process.Kill()
        if not error.Success():
            raise Exception("Could not stop: " + str(error))
    process = None

# thread selection
def select_thread(id):
    global process
    if not process:
        raise Exception("No process to work on")
    return process.SetSelectedThreadByID(id)

def selected_thread():
    global process
    if not process:
        raise Exception("No process to query")

    thread = process.GetSelectedThread()
    id = thread.GetThreadID()
    name = thread.GetName()
    frames = thread.GetNumFrames()
    return {
        "id": id,
        "name": name,
        "num_frames": frames
    }

# input/output to target
def get_stdout():
    global stdout_buffer
    buf = stdout_buffer
    stdout_buffer = ""
    return buf

def get_stderr():
    global stderr_buffer
    buf = stderr_buffer
    stderr_buffer = ""
    return buf

def push_stdin(data):
    global process
    if not process:
        raise Exception("No process to send data to")
    process.PutSTDIN(data)

# status and backtraces
def get_status():
    global status
    print(status)
    return status

def get_backtrace():
    global process
    if not process:
        raise Exception("No process to get traces of")
    bt = {}
    for thread in process.threads:

        bt_frames = []
        for frame in thread.frames:
            line = frame.GetLineEntry()
            bt_frames.append({
                "function": frame.GetFunctionName(),
                "file": line.file.fullpath,
                "line": line.GetLine(),
                "column": line.GetColumn(),
            })
        bt[str(thread.GetThreadID())] = bt_frames
    return bt

def get_backtrace_for_selected_thread():
    global process
    if not process:
        raise Exception("No process to get traces of")
    thread = process.GetSelectedThread()
    bt_frames = []
    for frame in thread.frames:
        line = frame.GetLineEntry()
        bt_frames.append({
            "function": frame.GetFunctionName(),
            "file": line.file.fullpath,
            "line": line.GetLine(),
            "column": line.GetColumn(),
        })
    return bt_frames

def get_threads():
    global process
    if not process:
        raise Exception("No process to query")

    threads = []
    for thread in process.threads:
        id = thread.GetThreadID()
        name = thread.GetName()
        frames = thread.GetNumFrames()
        threads.append({
            "id": id,
            "name": name,
            "num_frames": frames
        })
    return threads

def get_arguments(thread_id, frame_index):
    global process
    if not process:
        raise Exception("No process to query")
    thread = process.GetThreadByID(thread_id)
    frame = thread.frame[frame_index]
    result = {}

    for variable in frame.get_arguments():
        result[variable.GetName()] = variable.GetValue()
    return result

def get_local_variables(thread_id, frame_index):
    global process
    if not process:
        raise Exception("No process to query")
    thread = process.GetThreadByID(thread_id)
    frame = thread.frame[frame_index]
    result = {}

    for variable in frame.get_locals():
        result[variable.GetName()] = variable.GetValue()

    for variable in frame.get_statics():
        result[variable.GetName()] = variable.GetValue()
    return result

def get_all_variables(thread_id, frame_index):
    global process
    if not process:
        raise Exception("No process to query")
    thread = process.GetThreadByID(thread_id)
    frame = thread.frame[frame_index]
    result = {}

    for variable in frame.get_all_variables():
        result[variable.GetName()] = variable.GetValue()
    return result


# execute arbitrary command
def execute_lldb_command(command):
    interpreter = lldb_handle.GetCommandInterpreter()
    res = SBCommandReturnObject()
    HandleCommand(command, res)
    return res.Succeeded()

# breakpoints
def get_breakpoints():
    global target
    if not target:
        raise Exception("No target")
    breakpoints = []
    for i in xrange(0, target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        loc = bp.GetLocationAtIndex(0).GetAddress().GetLineEntry()
        breakpoints.append({
            "file": loc.file.fullpath,
            "line": loc.GetLine(),
            "enabled": bp.IsEnabled(),
            "condition": bp.GetCondition(),
            "ignore_count": bp.GetIgnoreCount(),
            "id": bp.id
        })
    return breakpoints

def set_breakpoint(filename, line_number, condition, ignore_count):
    global target
    if not target:
        raise Exception("No target")
    bp = target.BreakpointCreateByLocation(filename, line_number)
    if condition:
        bp.SetCondition(condition)
    if ignore_count:
        bp.SetIgnoreCount(ignore_count)
    return bp.id

def delete_breakpoint(id):
    global target
    if not target:
        raise Exception("No target")
    target.BreakpointDelete(id)

def enable_breakpoint(id):
    global target
    if not target:
        raise Exception("No target")
    for i in xrange(0, target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        if bp.id == id:
            bp.SetEnabled(True)
            break

def disable_breakpoint(id):
    global target
    if not target:
        raise Exception("No target")
    for i in xrange(0, target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        if bp.id == id:
            bp.SetEnabled(False)
            break

def disable_all_breakpoints():
    global target
    if not target:
        raise Exception("No target")
    target.DisableAllBreakpoints()

def enable_all_breakpoints():
    global target
    if not target:
        raise Exception("No target")
    target.EnableAllBreakpoints()

def delete_all_breakpoints():
    global target
    if not target:
        raise Exception("No target")
    target.DeleteAllBreakpoints()

def disable_breakpoints():
    global target, breakpoint_status
    if not target:
        raise Exception("No target")
    if len(breakpoint_status) > 0:
        return
    breakpoint_status = {}
    for i in xrange(0, target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        breakpoint_status[str(bp.id)] = bp.IsEnabled()
    disable_all_breakpoints()

def enable_breakpoints():
    global target, breakpoint_status
    if not target:
        raise Exception("No target")
    for i in xrange(0, target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        if breakpoint_status[str(bp.id)]:
            enable_breakpoint(bp.id)
    breakpoint_status = {}

#
# XMLRPC server
#

server = SimpleXMLRPCServer(("localhost", port), logRequests=True, allow_none=True)
server.register_introspection_functions()

# kill server
server.register_function(shutdown_server)

# load executable
server.register_function(prepare)

# start/stop/pause/step
server.register_function(start)
server.register_function(pause)
server.register_function(step_into)
server.register_function(step_over)
server.register_function(step_out)
server.register_function(stop)

# thread info
server.register_function(get_threads)
server.register_function(select_thread)
server.register_function(selected_thread)

# input/output
server.register_function(get_stdout)
server.register_function(get_stderr)
server.register_function(push_stdin)

# status
server.register_function(get_status)
server.register_function(get_backtrace)
server.register_function(get_backtrace_for_selected_thread)

# exec command
server.register_function(execute_lldb_command)

# get variables
server.register_function(get_arguments)
server.register_function(get_local_variables)
server.register_function(get_all_variables)

# breakpoint handling
server.register_function(get_breakpoints)
server.register_function(set_breakpoint)
server.register_function(delete_breakpoint)
server.register_function(enable_breakpoint)
server.register_function(disable_breakpoint)
server.register_function(disable_all_breakpoints)
server.register_function(enable_all_breakpoints)
server.register_function(delete_all_breakpoints)
server.register_function(disable_breakpoints)
server.register_function(enable_breakpoints)

try:
    server.serve_forever()
except KeyboardInterrupt:
    shutdown_server()
    sys.exit(0)
except Exception:
    sys.exit(0)
