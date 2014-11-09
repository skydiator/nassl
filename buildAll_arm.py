#!/usr/bin/python
from platform import architecture
from sys import platform, version_info
from os.path import join
from buildAll_config import OPENSSL_CONF_CMD, BUILD_DIR, PY_VERSION, OPENSSL_DIR, ZLIB_DIR, TEST_DIR, perform_build_task, create_folder
import os

NASSL_INSTALL_DIR = ''

# I've only tried building nassl on OS X 64 bits and Linux 32/64 bits
# Cross compile only work for ARM architecture.

if architecture()[0] == '64bit':
    if platform == 'darwin':
        OPENSSL_TARGET = 'darwin64-x86_64-cc'
        NASSL_INSTALL_DIR = join(BUILD_DIR, 'lib.macosx-10.9-intel-' + PY_VERSION + '/')
        OPENSSL_INSTALL_DIR = join(BUILD_DIR, 'openssl-darwin64')

    elif platform == 'linux2':
        OPENSSL_TARGET = 'linux-x86_64'
        NASSL_INSTALL_DIR = join(BUILD_DIR, 'lib.linux-x86_64-' + PY_VERSION + '/')
        OPENSSL_INSTALL_DIR = join(BUILD_DIR, 'openssl-linux64')

elif architecture()[0] == '32bit':
    if platform == 'linux2':
        OPENSSL_TARGET = 'linux-elf'
        NASSL_INSTALL_DIR = join(BUILD_DIR, 'lib.linux-i686-' + PY_VERSION + '/')
        OPENSSL_INSTALL_DIR = join(BUILD_DIR, 'openssl-linux32')


if NASSL_INSTALL_DIR == '':
    raise Exception('Plaftorm ' + platform + ' ' + architecture()[0] + ' not supported.')

# Setup the cross compile toolchain environment
# At this point make sure the toolchain path is exposed via $PATH 
CROSS_COMPILER = "arm-none-linux-gnueabi"
os.environ["TARGETMACH"] = CROSS_COMPILER
os.environ["CROSS"] = CROSS_COMPILER 
os.environ["CC"] = CROSS_COMPILER + "-gcc"
os.environ["LD"] = CROSS_COMPILER + "-ld"
os.environ["AS"] = CROSS_COMPILER + "-as"
os.environ["AR"] = CROSS_COMPILER + "-ar"

def main():
    # Create folder
    create_folder(TEST_DIR + '/nassl/')
    openssl_internal_dir = join(OPENSSL_INSTALL_DIR, "include", "openssl-internal")
    print "Creating dir " + PY_VERSION + " " +openssl_internal_dir
    create_folder(openssl_internal_dir)

    # Build Zlib
    ZLIB_BUILD_TASKS = [
        'CFLAGS="-fPIC" ./configure -static',
        'make clean',
        'make']

    perform_build_task('ZLIB', ZLIB_BUILD_TASKS, ZLIB_DIR)


    # Build OpenSSL
    OPENSSL_BUILD_TASKS = [
        OPENSSL_CONF_CMD(OPENSSL_TARGET, OPENSSL_INSTALL_DIR, ZLIB_DIR, ZLIB_DIR) + ' -fPIC' + ' shared os/compiler:arm-none-linux-gnueabi-',
        'make clean',
        #'make depend', # This makes building with Clang on OS X fail
        'make',
        # make test will fail if doing cross compile
        #'make test',
        'make install_sw', # don't build documentation, else will fail on Debian
        'cp %s %s/'%(join(OPENSSL_DIR, 'e_os.h'), OPENSSL_INSTALL_DIR),
        'cp %s %s/'%(join(OPENSSL_DIR, 'ssl', 'ssl_locl.h'), openssl_internal_dir)]

    perform_build_task('OPENSSL', OPENSSL_BUILD_TASKS, OPENSSL_DIR)

    # Build nassl
    NASSL_BUILD_TASKS = [
        'PYTHONXCPREFIX="%s" CC="%s" LDSHARED="%s" %s'%(NASSL_INSTALL_DIR, CROSS_COMPILER + '-gcc -pthread', CROSS_COMPILER + '-gcc -pthread -shared', 'python setup_arm.py build'),
        'cp -R ' + NASSL_INSTALL_DIR + '* ' + TEST_DIR]

    perform_build_task('NASSL', NASSL_BUILD_TASKS)


    # Test nassl
    #NASSL_TEST_TASKS = [
    #    'python -m unittest discover --pattern=*_Tests.py']

    #perform_build_task('NASSL Tests', NASSL_TEST_TASKS, TEST_DIR)


    print '=== All Done! Compiled module is available in ./test/nassl/ ==='

if __name__ == "__main__":
    main()
