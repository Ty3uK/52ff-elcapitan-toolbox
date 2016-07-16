#!/usr/bin/python
import argparse
import os
import shutil
import subprocess
import sys
from tempfile import mkstemp

BASE_PATH = os.path.dirname(os.path.realpath(__file__))

TOOLS_PATH = os.path.join(BASE_PATH, 'tools')
ACPI_PATH = os.path.join(BASE_PATH, 'acpi')
KEXTS_PATH = os.path.join(BASE_PATH, 'kexts')
SLE_PATH = '/System/Library/Extensions'
USB_PATH = os.path.join(BASE_PATH, 'usb')
VOODOO_DAEMON_PATH = os.path.join(BASE_PATH, 'voodooDaemon')

PATCHMATIC = os.path.join(TOOLS_PATH, 'patchmatic')
IASL = os.path.join(TOOLS_PATH, 'iasl')

SSDT_PATH = os.path.join(os.environ['HOME'], 'Library/ssdtPRGen/SSDT.aml')
DSDT_PATH = os.path.join(BASE_PATH, 'patches/dsdt')
IGPU_PATH = os.path.join(BASE_PATH, 'patches/ssdt')

DSDT_AML = os.path.join(ACPI_PATH, 'DSDT.aml')
DSDT_DSL = os.path.join(ACPI_PATH, 'DSDT.dsl')
DSDT_HEX = os.path.join(ACPI_PATH, 'DSDT.hex')
IGPU_AML = os.path.join(ACPI_PATH, 'SSDT-3.aml')
IGPU_DSL = os.path.join(ACPI_PATH, 'SSDT-3.dsl')
IGPU_HEX = os.path.join(ACPI_PATH, 'SSDT-3.hex')

SSDT_UIA_HEX = os.path.join(ACPI_PATH, 'SSDT-UIA.hex')
SSDT_XOSI_HEX = os.path.join(ACPI_PATH, 'SSDT-XOSI.hex')

VOODOO_PLIST = os.path.join(
    VOODOO_DAEMON_PATH,
    'org.rehabman.voodoo.driver.Daemon.plist'
)
VOODOO_BIN = os.path.join(VOODOO_DAEMON_PATH, 'VoodooPS2Daemon')

FNULL = open(os.devnull, 'w')

UNKNOWN_OBJ_1 = "External (_SB_.PCI0.PEG0, UnknownObj)"
UNKNOWN_OBJ_2 = "External (_SB_.PCI0.PEG0.PEGP, UnknownObj)"


def print_progress(message, only_when_done=False):
    def decorate(function):
        def wrapper(*args, **kvargs):
            if not only_when_done:
                sys.stdout.write(' - {0}...\r'.format(message))
                sys.stdout.flush()

            function(*args, **kvargs)

            sys.stdout.write(' - {0}...Done!\n'.format(message))
        return wrapper
    return decorate


def recreate_acpi_folder():
    if os.path.exists(ACPI_PATH):
        shutil.rmtree(ACPI_PATH, ignore_errors=True)
    os.makedirs(ACPI_PATH)


@print_progress("Extracting ACPI Tables")
def extract_acpi():
    os.chdir(ACPI_PATH)
    subprocess.call([PATCHMATIC, '-extract'])
    for file in os.listdir(ACPI_PATH):
        if not (
            (file.lower() == 'dsdt.aml') or (file.lower() == 'ssdt-3.aml')
        ):
            os.remove(os.path.join(ACPI_PATH, file))


@print_progress("Disassembling ACPI Tables")
def disassemble_acpi():
    subprocess.call(
        [IASL, '-da', '-dl', DSDT_AML, IGPU_AML],
        stdout=FNULL,
        stderr=subprocess.STDOUT
    )


def remove_assembled_acpi():
    os.remove(DSDT_AML)
    os.remove(IGPU_AML)


def patch_acpi():
    @print_progress("Patching DSDT")
    def patch_dsdt():
        for file in os.listdir(DSDT_PATH):
            subprocess.call(
                [
                    PATCHMATIC,
                    DSDT_DSL,
                    os.path.join(DSDT_PATH, file),
                    DSDT_DSL
                ],
                stdout=FNULL,
                stderr=subprocess.STDOUT
            )

        fh, abs_path = mkstemp()
        with open(abs_path, 'w') as new_file:
            with open(os.path.join(ACPI_PATH, 'DSDT.dsl')) as old_file:
                for line in old_file:
                    if not (
                        (line.strip() == UNKNOWN_OBJ_1) or
                        (line.strip() == UNKNOWN_OBJ_2)
                    ):
                        new_file.write(line)
        os.close(fh)
        if os.path.exists('./dsdt.dsl'):
            os.remove('./dsdt.dsl')
        shutil.move(abs_path, './DSDT.dsl')

    @print_progress("Patching IGPU")
    def patch_igpu():
        os.chdir(ACPI_PATH)
        for file in os.listdir(IGPU_PATH):
            subprocess.call(
                [
                    PATCHMATIC,
                    IGPU_DSL,
                    os.path.join(IGPU_PATH, file),
                    IGPU_DSL
                ],
                stdout=FNULL,
                stderr=subprocess.STDOUT
            )

    patch_dsdt()
    patch_igpu()


@print_progress("Compiling Patched ACPI Tables")
def compile_patched_acpi():
    os.chdir(ACPI_PATH)
    for file in os.listdir(ACPI_PATH):
        if file[-3:] == 'dsl':
            subprocess.call(
                [IASL, '-tc', file],
                stdout=FNULL,
                stderr=subprocess.STDOUT
            )

    os.remove(DSDT_DSL)
    if os.path.exists(DSDT_HEX):
        os.remove(DSDT_HEX)
    os.remove(IGPU_DSL)
    if os.path.exists(IGPU_HEX):
        os.remove(IGPU_HEX)


@print_progress("Generating SSDT")
def generate_ssdt():
    p = subprocess.Popen(
        os.path.join(TOOLS_PATH, 'ssdtPRGen.sh'),
        stdout=FNULL,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    p.stdin.write('n')
    p.stdin.write('n')
    p.communicate()[0]
    p.stdin.close()

    if os.path.exists(SSDT_PATH):
        if not os.path.exists(ACPI_PATH):
            os.makedirs(ACPI_PATH)
        shutil.copyfile(SSDT_PATH, os.path.join(ACPI_PATH, 'SSDT.aml'))


@print_progress("Requesting superuser privileges", only_when_done=True)
def promt_password():
    subprocess.call('sudo true', shell=True)


@print_progress("Copying kexts")
def copy_kexts():
    for file in os.listdir(KEXTS_PATH):
        if file[-5:] == '.kext':
            subprocess.call(
                'sudo cp -R %s %s' % (
                    os.path.join(KEXTS_PATH, file),
                    SLE_PATH
                ),
                shell=True
            )
            subprocess.call(
                'sudo chmod -R 755 %s' % os.path.join(SLE_PATH, file),
                shell=True
            )
            subprocess.call(
                'sudo chown -R root:wheel %s' % os.path.join(SLE_PATH, file),
                shell=True
            )

            if file[:-5] == 'VoodooPS2Controller':
                subprocess.call(
                    'sudo cp %s /Library/LaunchDaemons' % VOODOO_PLIST,
                    shell=True
                )
                subprocess.call(
                    'sudo cp %s /usr/bin' % VOODOO_BIN,
                    shell=True
                )


@print_progress("Rebuilding kext cache")
def rebuild_kext_cache():
    subprocess.call(
        'sudo kextutil %s' % os.path.join(SLE_PATH, 'AppleHDA_ALC283.kext'),
        shell=True,
        stdout=FNULL,
        stderr=subprocess.STDOUT
    )
    subprocess.call(
        'sudo touch %s && sudo kextcache -u /' % SLE_PATH,
        shell=True,
        stdout=FNULL,
        stderr=subprocess.STDOUT
    )


@print_progress("Compiling USB ports config")
def compile_usb_ports_config():
    os.chdir(ACPI_PATH)
    for file in os.listdir(USB_PATH):
        subprocess.call(
            [
                IASL,
                '-p',
                os.path.join(ACPI_PATH, file),
                '-tc',
                os.path.join(USB_PATH, file)
            ],
            stdout=FNULL,
            stderr=subprocess.STDOUT
        )

    os.remove(SSDT_XOSI_HEX)
    os.remove(SSDT_UIA_HEX)

if __name__ == "__main__":
    if not os.path.exists(TOOLS_PATH):
        print_progress("Tools folder doesn't exists. Exiting...")
        exit()

    parser = argparse.ArgumentParser(
        description="Acer Aspire V3-371-52FF El Capitan toolbox",
        epilog="Credits: ssdtPRGen.sh by PikerAlpha, ACPI patches and kexts by RehabMan. Project located at: https://github.com/Ty3uK/52ff-elcapitan-toolbox"
    )
    parser.add_argument(
        "-e",
        "--extract",
        help="extract needed ACPI tables and decompile it",
        action="store_true"
    )
    parser.add_argument(
        "-p",
        "--patch",
        help="apply patches located at `patches` subfolder",
        action="store_true"
    )
    parser.add_argument(
        "-c",
        "--compile",
        help="compile ACPI tables",
        action="store_true"
    )
    parser.add_argument(
        "-u",
        "--usb",
        help="compile USB ports config",
        action="store_true"
    )
    parser.add_argument(
        "-k",
        "--install-kexts",
        help="install kexts located at `kexts` subfolder",
        action="store_true"
    )
    parser.add_argument(
        "-gs",
        "--ssdt",
        help="generate SSDT.aml",
        action="store_true"
    )
    parser.add_argument(
        "-a",
        "--all",
        help="run all actions",
        action="store_true"
    )
    args = parser.parse_args()

    print("#" * 80)

    try:
        if len(sys.argv) is 1:
            parser.print_help()
        else:
            if args.install_kexts or args.all:
                promt_password()
                copy_kexts()
                rebuild_kext_cache()
            if args.extract or args.all:
                recreate_acpi_folder()
                extract_acpi()
                disassemble_acpi()
                remove_assembled_acpi()
            if args.patch or args.all:
                patch_acpi()
            if args.compile or args.all:
                compile_patched_acpi()
            if args.ssdt or args.all:
                generate_ssdt()
            if args.usb or args.all:
                compile_usb_ports_config()
    except KeyboardInterrupt:
        pass

    print("#" * 80)
