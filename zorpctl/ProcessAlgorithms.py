############################################################################
##
## Copyright (c) 2000-2015 BalaBit IT Ltd, Budapest, Hungary
## Copyright (c) 2015-2018 BalaSys IT Ltd, Budapest, Hungary
##
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program; if not, write to the Free Software Foundation, Inc.,
## 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##
############################################################################

import os, sys, signal, time, subprocess, datetime
import Zorp.Config
from zorpctl.szig import SZIG, SZIGError
from zorpctl.CommandResults import CommandResultSuccess, CommandResultFailure
from zorpctl.ZorpctlConf import ZorpctlConfig

class ProcessStatus(object):
    def __init__(self, name):
        self.name = name
        self.reload_timestamp = 0
        self.details = None
        self.msg = ""
        self.reloaded = True
        self.threads = 0
        self.pid = 0

    def __str__(self):
        status = self.msg
        if self.pid > 0:
            status += "running"
        if not self.reloaded:
            status += ", policy NOT reloaded"
        if self.threads > 0:
            status += ", %d threads active" % self.threads
        if self.pid > 0:
            status += ", pid %d" % self.pid
        if self.details:
            status += "\n%s" % self.details
        return status

class GUIStatus(object):
    def __init__(self, name):
        self.name = name
        self.processnum = name.split('#')[-1]
        self.reload_timestamp = 0
        self.details = None
        self.msg = ""

    def __str__(self):
        status = '"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s"' % (self.name,
                 self.processnum, self.running, self.pid,
                 self.threads_running, self.thread_number, self.thread_rate_avg1,
                 self.thread_rate_avg5, self.thread_rate_avg15)
        return status

class ProcessAlgorithm(object):

    def __init__(self):
        self.ZORPCTLCONF = ZorpctlConfig.Instance()
        try:
            self.sbindir = self.ZORPCTLCONF['ZORP_SBINDIR']
            self.pidfiledir = self.ZORPCTLCONF['ZORP_PIDFILEDIR'] + "/"
        except KeyError as e:
            e.message = "You must specify the install directory of Zorp executable \
like ZORP_LIBDIR=='/usr/lib/zorp' and the directory where Zorp puts it's pid files \
like ZORP_PIDFILEDIR='/var/run/zorp', put it in to the zorpctl's configuration file!"
            raise e
        self.force = False
        self.instance = None
        #variable indicates if force is active by force commands

    def isRunning(self, process):
        """
        Opening the right pidfile in the pidfile dir,
        checking if there is a running process with that pid,
        returning True if there is.

        FIXME: Delete pid file if there is no runnig processes with that pid
        """

        pid = self.getProcessPid(process)
        if not pid:
            if pid.value == "Permission denied":
                return CommandResultFailure(pid.value)
            else:
                return CommandResultFailure('Process not running')

        try:
            open('/proc/' + str(pid) + '/status')
        except IOError:
            return CommandResultFailure(
                'Invalid pid file no running process with pid {}!'.format(pid)
            )

        return CommandResultSuccess('Running')

    def _getProcessPidPath(self, process):
        return self.pidfiledir  + '/zorp-' + process + '.pid'

    def getProcessPid(self, process):
        try:
            file_path = self._getProcessPidPath(process)
            pid_file = open(file_path)
            pid = int(pid_file.read())
            pid_file.close()
        except IOError as e:
            return CommandResultFailure(
                "'Can not open pid file '{}'".format(file_path),
                e.message
            )

        return pid

    def removeProcessPid(self, process):
        try:
            file_path = self._getProcessPidPath(process)
            if os.path.exists(file_path):
                os.remove(file_path)
        except IOError as e:
            return CommandResultFailure(
                "Could not remove pid file '{}'".format(file_path),
                e.message
            )

    def setInstance(self, instance):
        self.instance = instance

    def run(self):
        if self.instance:
            return self.execute()
        else:
            return CommandResultFailure('No instance added!')


class StartAlgorithm(ProcessAlgorithm):

    def __init__(self, use_systemd=False):
        self.use_systemd = use_systemd
        super(StartAlgorithm, self).__init__()
        try:
            self.start_timeout = self.ZORPCTLCONF['START_WAIT_TIMEOUT']
        except KeyError:
            self.start_timeout = 10

    def getSystemdServiceName(self):
        return 'zorp{}@{}.service'.format(
            Zorp.Config.config.options.package_suffix,
            self.instance.name
        )

    def errorHandling(self):
        if self.use_systemd:
            ret = subprocess.call(
                ['/bin/systemctl', 'is-active', '--quiet', self.getSystemdServiceName()]
            )
            if not ret:
                return CommandResultSuccess('Running')
        else:
            running = self.isRunning(self.instance.process_name)
            if running:
                return CommandResultSuccess('Process is already running')

        valid = self.isValidInstanceForStart()
        if not valid:
            return valid

    def isValidInstanceForStart(self):
        if not 0 <= self.instance.process_num < self.instance.number_of_processes:
            return CommandResultFailure(
                'Number {} must be between [0..{})'.format(
                    self.instance.process_num,
                    self.instance.number_of_processes
                )
            )

        if not self.instance.auto_start and not self.force:
            return CommandResultFailure('Not started, because no-auto-start is set')

        return CommandResultSuccess()

    def assembleStartCommand(self):
        command = [self.sbindir + '/zorp', '--as', self.instance.name]
        command.extend(self.instance.zorp_argument_list)
        command.append('--slave' if self.instance.process_num else '--master')
        command.append(self.instance.process_name)

        if self.instance.enable_core:
            command.append('--enable-core')
        if not self.instance.auto_restart:
            command.extend(['--process-mode', 'background'])
        for arg in command:
            if arg.startswith(("'", '"')) and (arg[0] == arg[-1]):
                command[command.index(arg)] = arg[1:-1]

        return command

    def waitTilTimoutToStart(self):
        t = 1
        try:
            delay = self.ZORPCTLCONF['STOP_CHECK_DELAY']
        except KeyError:
            delay = 1
        while t <= self.start_timeout and not self.isRunning(self.instance.process_name):
            time.sleep(delay)
            t += 1

    def start_with_systemd(self):
        try:
            subprocess.check_call(
                ['/bin/systemctl', 'start', self.getSystemdServiceName()]
            )
        except:
            return CommandResultFailure(
                "Error invoking 'systemctl start zorp{}@{}.service'".format(
                    Zorp.Config.config.options.package_suffix,
                    self.instance.name
                )
            )

        running = self.isRunning(self.instance.process_name)
        if running:
            return CommandResultSuccess(running)
        else:
            return CommandResultFailure('Failed to start')

    def start(self):
        args = self.assembleStartCommand()

        environment = None

        try:
            subprocess.Popen(args, env=environment)
        except OSError:
            pass
        self.waitTilTimoutToStart()

        running = self.isRunning(self.instance.process_name)
        if running:
            return CommandResultSuccess(running)
        else:
            return CommandResultFailure('Did not start in time')

    def execute(self):
        error = self.errorHandling()
        if error is not None:
            return error

        if self.use_systemd:
            return self.start_with_systemd()
        else:
            return self.start()


class StopAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(StopAlgorithm, self).__init__()
        try:
            self.stop_timeout = self.ZORPCTLCONF['STOP_CHECK_TIMEOUT']
        except KeyError:
            self.stop_timeout = 5

        self.pid = None

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            # Ignore not running process
            return CommandResultSuccess(running.msg)

    def waitTilTimeoutToStop(self):
        t = 1
        try:
            delay = self.ZORPCTLCONF['STOP_CHECK_DELAY']
        except KeyError:
            delay = 1
        while t <= self.stop_timeout and self.isRunning(self.instance.process_name):
            time.sleep(delay)
            t += 1

    def killProcess(self, sig):
        self.pid = self.getProcessPid(self.instance.process_name)

        try:
            os.kill(self.pid, sig)
            if self.force:
                self.removeProcessPid(self.instance.process_name)
        except OSError as e:
            return CommandResultFailure(e.message)

        return CommandResultSuccess()

    def stop(self):
        sig = signal.SIGKILL if self.force else signal.SIGTERM
        isKilled = self.killProcess(sig)
        if not isKilled:
            return isKilled

        self.waitTilTimeoutToStop()
        if self.isRunning(self.instance.process_name):
            return CommandResultFailure(
                "Did not exit in time (pid='{}', signo='{}', timeout='{}')".format(
                    self.pid, sig, self.stop_timeout
                )
            )
        else:
            return CommandResultSuccess('Stopped')

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        return self.stop()

class ReloadAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(ReloadAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            # Ignore not running process
            return CommandResultSuccess(running.msg)

        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.message)

    def reload(self):
        self.szig.reload()
        if self.szig.reload_result():
            result = CommandResultSuccess('Reload successful')
        else:
            result = CommandResultFailure('Reload failed')
        return result

    def execute(self):
        error = self.errorHandling()
        if error != None:
            error.value = self.instance.process_name
            return error

        try:
            reloaded = self.reload()
        except SZIGError as e:
            reloaded = CommandResultFailure('Error while communicating through szig: ' + e.msg)
        if not reloaded:
            reloaded.value = self.instance.process_name
        return reloaded

class DeadlockCheckAlgorithm(ProcessAlgorithm):

    def __init__(self, value=None):
        self.value = value
        super(DeadlockCheckAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.message)

    def getDeadlockcheck(self):
        return CommandResultSuccess('Deadlockcheck={}'.format(self.szig.deadlockcheck))

    def setDeadlockcheck(self, value):
        self.szig.deadlockcheck = value
        return self.getDeadlockcheck()

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            if self.value != None:
                return self.setDeadlockcheck(self.value)
            else:
                return self.getDeadlockcheck()
        except SZIGError as e:
            return CommandResultFailure('Error while communicating through szig: ' + e.msg)

class LogLevelAlgorithm(ProcessAlgorithm):

    GET = 'G'
    SET = 'S'
    DECREMENT = 'D'
    INCREMENT = 'I'

    def __init__(self, mode=GET, value=None):
        self.mode = mode
        self.value = value
        super(LogLevelAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running

        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.message)

    def getLevel(self):
        return CommandResultSuccess(
            "verbose_level={}, logspec='{}'".format(self.szig.loglevel, self.szig.logspec),
            self.szig.loglevel
        )

    def setLevel(self, value):
        self.szig.loglevel = value
        return CommandResultSuccess('New verbose_level={}'.format(value))

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            actual_value = self.getLevel().value
            if self.mode == self.GET:
                return self.getLevel()
            elif self.mode == self.SET and self.value >= 0 and self.value <= 10:
                return self.setLevel(self.value)
            elif self.mode == self.INCREMENT and actual_value < 10:
                return self.setLevel(actual_value + 1)
            elif self.mode == self.DECREMENT and actual_value > 0:
                return self.setLevel(actual_value - 1)
            else:
                return CommandResultFailure('Log level is out of range')
        except SZIGError as e:
            return CommandResultFailure('Error while communicating through szig: ' + e.msg)

class GetProcInfoAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(GetProcInfoAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        pid = self.getProcessPid(self.instance.process_name)
        try:
            self.procinfo_file = open("/proc/%s/stat" % pid, 'r')
        except IOError:
            return CommandResultFailure('Can not open /proc/{}/stat'.format(pid))

    def getProcInfo(self):
        values = self.procinfo_file.read().split()
        self.procinfo_file.close()
        keys = ("pid", "comm", "state", "ppid", "pgrp", "session", "tty_nr",
                "tpgid", "flags", "minflt", "cminflt", "majflt", "cmajflt",
                "utime", "stime", "cutime", "cstime", "priority", "nice",
                "_dummyzero", "itrealvalue", "starttime", "vsize", "rss",
                "rlim", "startcode", "endcode", "startstack", "kstkesp",
                "kstkeip", "signal", "blocked", "sigignore", "sigcatch",
                "wchan", "nswap", "cnswap", "exit_signal", "processor")
        proc_info = {}
        for value, key in zip(values, keys):
            proc_info[key] = value
        return proc_info

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        return self.getProcInfo()

class PidAlgorithm(ProcessAlgorithm):
    def __init__(self):
        super(PidAlgorithm, self).__init__()

    def execute(self):
        status = ProcessStatus(self.instance.process_name)
        status.pid = self.getProcessPid(self.instance.process_name)
        return status

class StatusAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(StatusAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.message)

    def status(self):
        status = ProcessStatus(self.instance.process_name)
        status.pid = self.getProcessPid(self.instance.process_name)

        status.threads = int(self.szig.get_value('stats.threads_running'))
        status.policy_file = self.szig.get_value('info.policy.file')
        status.timestamp_szig = self.szig.get_value('info.policy.file_stamp')
        status.reload_timestamp = self.szig.get_value('info.policy.reload_stamp')
        status.timestamp_os = os.path.getmtime(status.policy_file)
        status.reloaded = str(status.timestamp_szig) == str(status.timestamp_os).split('.')[0]

        return status

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            return self.status()
        except SZIGError as e:
            return CommandResultFailure('Error while communicating through szig: ' + e.msg)

class GUIStatusAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(GUIStatusAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            self.status.pid = "missing"
            self.status.running = "missing"
            self.status.threads_running = "missing"
            self.status.thread_number = "missing"
            self.status.thread_rate_avg1 = "missing"
            self.status.thread_rate_avg5 = "missing"
            self.status.thread_rate_avg15 = "missing"
            return self.status
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.message)

    def gui_status(self):
        self.status.pid = self.getProcessPid(self.instance.process_name)

        self.status.running = "running"
        self.status.threads_running = self.szig.get_value('stats.threads_running')
        self.status.thread_number = self.szig.get_value('stats.thread_number')
        self.status.thread_rate_avg1 = self.szig.get_value('stats.thread_rate_avg1')
        self.status.thread_rate_avg5 = self.szig.get_value('stats.thread_rate_avg5')
        self.status.thread_rate_avg15 = self.szig.get_value('stats.thread_rate_avg15')

        return self.status

    def execute(self):
        self.status = GUIStatus(self.instance.process_name)
        error = self.errorHandling()
        if error != None:
            return error

        try:
            return self.gui_status()
        except SZIGError as e:
            return CommandResultFailure('Error while communicating through szig: ' + e.msg)

class DetailedStatusAlgorithm(ProcessAlgorithm):

    def __init__(self):
        super(DetailedStatusAlgorithm, self).__init__()
        self.uptime_filename = '/proc/uptime'
        self.proc_stat_filename = '/proc/stat'

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.stat_file = open(self.proc_stat_filename, 'r')
        except IOError:
            return CommandResultFailure('Can not open ' + self.proc_stat_filename)
        try:
            uptime_file = open(self.uptime_filename, 'r')
            uptime_file.close()
        except IOError:
            return CommandResultFailure('Can not open ' + self.uptime_filename)

    def _getIdleJiffies(self):
        for buf in self.stat_file:
            if (buf[:4] == "cpu "):
                idle_jiffies = float(buf.split()[4])
                break
        self.stat_file.close()
        return idle_jiffies

    def _getIdleSec(self):
        uptime_file = open(self.uptime_filename, 'r')
        idle_sec = float(uptime_file.readline().split()[1])
        uptime_file.close()

        return idle_sec

    def getJiffiesPerSec(self):
        idle_jiffies = self._getIdleJiffies()
        idle_sec = self._getIdleSec()

        jiffies_per_sec = int(round(5 + (idle_jiffies/idle_sec), -1))
        return jiffies_per_sec

    def _getProcInfo(self):
        algorithm = GetProcInfoAlgorithm()
        algorithm.setInstance(self.instance)
        return algorithm.run()

    def _getLoaded(self, stamp):
        return datetime.datetime.fromtimestamp(float(stamp))

    def _getTimes(self, proc_info, jps):
        usertime = float(proc_info['utime']) / jps
        usermin = int(usertime / 60)
        usertime -= usermin * 60

        systime = float(proc_info["stime"]) / jps
        sysmin = int(systime / 60)
        systime -= sysmin * 60

        realtime = usertime + systime
        realmin = int(realtime / 60)
        realtime -= realmin * 60

        return (realmin, realtime, usermin, usertime, sysmin, systime)

    def _getStartTime(self, proc_info, jps):
        uptime_file = open(self.uptime_filename, 'r')
        uptime_float = float(uptime_file.readline().split()[0])
        uptime_file.close()
        uptime = datetime.datetime.fromtimestamp(uptime_float)
        uptime_timedelta = uptime - datetime.datetime.fromtimestamp(0)

        now = datetime.datetime.now()
        starttime = (now - (uptime_timedelta) +
                            (datetime.datetime.fromtimestamp(float(proc_info["starttime"]) / jps) -
                             datetime.datetime.fromtimestamp(0)))
        return starttime

    def assembleDetails(self, status, proc_info, jps):
        PAGESIZE = 4 #getconf PAGESIZE in kB (4096)
        details = "started at: %s\n" % self._getStartTime(proc_info, jps)
        details += "policy: file=%s, loaded=%s\n" % (status.policy_file, self._getLoaded(status.reload_timestamp))
        details += "cpu: real=%d:%f, user=%d:%f, sys=%d:%f\n" % self._getTimes(proc_info, jps)
        details += "memory: vsz=%skB, rss=%skB" % (int(proc_info["vsize"])/1024, int(proc_info["rss"]) * PAGESIZE)

        return details

    def detailedStatus(self):
        statusalgorithm = StatusAlgorithm()
        statusalgorithm.setInstance(self.instance)
        status = statusalgorithm.run()

        jps = self.getJiffiesPerSec()
        proc_info = self._getProcInfo()

        status.details = self.assembleDetails(status, proc_info, jps)

        return status

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        return self.detailedStatus()

class SzigWalkAlgorithm(ProcessAlgorithm):

    def __init__(self, root=""):
        self.root = root
        super(SzigWalkAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            # Ignore not running process
            return CommandResultSuccess(running.msg)

        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.message)
        return None

    def getChilds(self, node):
        child = self.szig.get_child(node)
        if child:
            result = {}
            result[child.split('.')[-1]] = self.walk(child)
            sibling = self.szig.get_sibling(child)
            while sibling:
                result[sibling.split('.')[-1]] = self.walk(sibling)
                sibling = self.szig.get_sibling(sibling)
            return result
        else:
            return None

    def walk(self, node):
        value = self.szig.get_value(node)
        if value != None:
            return value
        else:
            return self.getChilds(node)

    def execute(self):
        def _prepend_instance_name(tree):
            return {self.instance.process_name : tree}

        error = self.errorHandling()
        if error != None:
            return error

        try:
            if self.root:
                szig_dict = _prepend_instance_name({self.root : self.walk(self.root)})
            else:
                szig_dict = _prepend_instance_name(self.walk(self.root))

            return CommandResultSuccess(value=szig_dict)
        except SZIGError as e:
            return CommandResultFailure('Error while communicating through szig: ' + e.msg)

class AuthorizeAlgorithm(ProcessAlgorithm):

    ACCEPT = True
    REJECT = False

    def __init__(self, behaviour, session_id, description):
        self.behaviour = behaviour
        self.session_id = session_id
        self.description = description
        super(AuthorizeAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.message)
        return None

    def accept(self):
        try:
            result = self.szig.authorize_accept(self.session_id, self.description)
            return CommandResultSuccess(result)
        except SZIGError as e:
            return CommandResultFailure(e.msg)

    def reject(self):
        try:
            result = self.szig.authorize_reject(self.session_id, self.description)
            return CommandResultSuccess(result)
        except SZIGError as e:
            return CommandResultFailure(e.msg)

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            if self.behaviour:
                return self.accept()
            else:
                return self.reject()
        except SZIGError as e:
            return CommandResultFailure('Error while communicating through szig: ' + e.msg)

class StopSessionAlgorithm(ProcessAlgorithm):

    def __init__(self, session_id):
        self.session_id = session_id
        super(StopSessionAlgorithm, self).__init__()

    def errorHandling(self):
        running = self.isRunning(self.instance.process_name)
        if not running:
            return running
        try:
            self.szig = SZIG(self.instance.process_name)
        except IOError as e:
            return CommandResultFailure(e.message)

    def execute(self):
        error = self.errorHandling()
        if error != None:
            return error

        try:
            result = self.szig.stop_session(self.session_id)
            return CommandResultSuccess(result)
        except SZIGError as e:
            return CommandResultFailure('Error while communicating through szig: ' + e.msg)

