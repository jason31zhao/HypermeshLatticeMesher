import time
from typing import List
import os
import glob
import psutil


class HyperWorksStarter:
    """
    Hypermesh Starter Class (Windows only currently)
    version should be above 2021 - else: check paths!
    """

    # Change this according to your system
    ALTAIR_VERSION = "2022"  # user input

    # File paths
    OPTISTRUCT_PROCESS_NAME = f"optistruct_{ALTAIR_VERSION}_win64.exe"
    ALTAIR_HOME = os.environ["ProgramFiles"] + f"\\Altair\\{ALTAIR_VERSION}"
    ALTAIR_HOME = ALTAIR_HOME.replace("\\", "/")
    PATH_HYPERMESH = ALTAIR_HOME + "\\hwdesktop\\hm\\bin\\win64\\hmopengl.exe"
    PATH_HYPERVIEW = ALTAIR_HOME + "\\hwdesktop\\hw\\bin\\win64\\hw.exe"

    def __init__(self, working_dir: str, model_name_no_ext: str) -> None:
        self.working_dir = working_dir.replace("\\", "/")
        self.model_name = model_name_no_ext
        self.script_path = self.working_dir + "/" + self.model_name + ".tcl"
        self.script_path = self.script_path.replace("\\", "/")
        print(self.script_path)
        self.tcl_commands = []

    def initialize_tcl_commands() -> List:
        tcl_commands = []
        tcl_commands.append(
            f'*templatefileset "{HyperWorksStarter.ALTAIR_HOME}/hwdesktop/templates/feoutput/optistruct/optistruct"'
        )
        return tcl_commands

    def initialize_tcl_commands_hyperview() -> List:
        tcl_commands = []
        return tcl_commands

    def runHyperMesh(self, batch=False, wait=False):
        import subprocess

        # Hide Output of the shell - relax!
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        if batch:
            process = subprocess.Popen(
                [
                    self.PATH_HYPERMESH.replace("hmopengl", "hmbatch"),
                    "-tcl",
                    self.script_path,
                ],
                startupinfo=startupinfo,
            )

        else:
            process = subprocess.Popen(
                [self.PATH_HYPERMESH, "-tcl", self.script_path], startupinfo=startupinfo
            )

        print("Waiting for Hypermesh Process to Finish")
        process.wait()
        # batch needs special attention:
        if batch:
            while checkIfProcessRunning("hmbatch.exe"):
                print("Waiting for Hypermesh (hmbatch) Process to Finish")
                time.sleep(1)
        else:
            while checkIfProcessRunning("hmopengl.exe"):
                print("Waiting for Hypermesh (hmopengl) Process to Finish")
                time.sleep(1)

        # Wait in case of a run
        if wait:
            while checkIfProcessRunning(self.OPTISTRUCT_PROCESS_NAME):
                print("Waiting for Optistruct Process to Finish")
                time.sleep(1)

            print("Finished Altair Run")

    def runHyperview(self, batch=False, wait=False):
        """
        based on running hypermesh
        """
        import subprocess

        # Hide Output of the shell - relax!
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # if (hidden):
        # startupinfo.wShowWindow = subprocess.SW_HIDE

        # print(script_path)
        if batch:
            process = subprocess.Popen(
                [self.PATH_HYPERVIEW, "-b", "-tcl", self.script_path],
                startupinfo=startupinfo,
            )

        else:
            process = subprocess.Popen(
                [self.PATH_HYPERVIEW, "-tcl", self.script_path], startupinfo=startupinfo
            )

        if wait:
            print("Waiting for Hyperview Process to Finish")
            process.wait()
        # batch needs special attention:
        if wait:
            if checkIfProcessRunning("hw.exe"):
                print("Waiting for Hyperview (hw.exe) Process to Finish")
                time.sleep(1)

            print("Finished Hyperview Run")

    def add_export_and_run_options(self, fem_path: str, user_param: str):
        """
        Adds the lines for exporting a .fem file and run options
        Here is a list of the most important parameters for reference:
        -optskip : skips optimization (analysis only)
        -len 10000 : amount of RAM in mb
        -nproc 8 : number of processors: 8
        Seperate them by space. e.g. -optskip -len 10000 -nproc 8
        """
        self.tcl_commands.append('*createstringarray 1 "CONNECTORS_SKIP "')
        altair_home_exec = self.ALTAIR_HOME.replace("\\", "/")
        self.tcl_commands.append("hm_answernext yes")  # overwrite
        self.tcl_commands.append(
            f'*feoutputwithdata "{altair_home_exec}/hwdesktop/templates/feoutput/optistruct/optistruct" "{fem_path}" 1 0 2 1 1'
        )
        self.tcl_commands.append(
            f'exec "{altair_home_exec}/hwsolvers/scripts/optistruct.bat" "{fem_path}" {user_param} &'
        )
        # no gui (later)
        # tcl_commands.append(f"exec cmd /K START \"{altair_home_exec}/hwsolvers/scripts/optistruct.bat\" \"{export_path}\" {user_param} &")
        # self.tcl_commands.append("*quit 1")

    def write_script(
        self, tcl_commands: List[str], calc_dir: str, run: bool, user_param: str
    ):
        """
        writes the script and runs it. For the list or user_param, see the HyperWorksStarter method
        """
        self.tcl_commands = [
            line for line in tcl_commands
        ]  # copy as we don't want to change the original data
        calc_dir = calc_dir.replace("\\", "/")  # hypermesh does not like \
        self.tcl_commands.insert(0, f"cd {calc_dir}")  # change working directory
        fem_path = calc_dir + "/" + self.model_name + ".fem"
        if run:
            self.add_export_and_run_options(fem_path, user_param)

        with open(self.script_path, "w") as tcl_file:
            for line in self.tcl_commands:
                tcl_file.write("%s\n" % line)

    def write_script_hyperview(self, calc_dir: str, tcl_commands: List[str]):
        """
        placeholder for now
        """
        self.tcl_commands = [
            line for line in tcl_commands
        ]  # copy as we don't want to change the original data
        calc_dir = calc_dir.replace("\\", "/")  # hypermesh does not like \
        self.tcl_commands.insert(0, f"cd {calc_dir}")  # change working directory
        with open(self.script_path, "w") as tcl_file:
            for line in self.tcl_commands:
                tcl_file.write("%s\n" % line)

    def clean_up_simulation_dir(self, simulation_dir: str) -> None:
        """
        Removes Files left from the solver which aren't necessary to the user
        """
        filelist = glob.glob(os.path.join(simulation_dir, "*~"))
        for f in filelist:
            print("Deleted File: " + f + ", (cleanup Sim Dir)")
            os.remove(f)


def checkIfProcessRunning(processName):
    """
    Check if there is any running process that contains the given name processName.
    """
    # Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False
