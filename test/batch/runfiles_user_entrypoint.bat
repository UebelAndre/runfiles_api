@echo off
setlocal enableextensions enabledelayedexpansion
@REM A small binary for accessing runfiles.
@REM
@REM Implements the subject contract in `CONTRIBUTING.md`. The runfiles library
@REM is appended below in its inline mode, so this script must `exit /b`
@REM before reaching it.

if /i "%~1"=="--bench" (
    echo Benchmarking is not supported: batch has no sub-millisecond clock. >&2
    exit /b 5
)
if "%~1"=="" (
    echo Usage: %~nx0 [--bench ITERATIONS] ^<rlocationpath^>... >&2
    echo Example: %~nx0 workspace/path/to/file.txt >&2
    exit /b 1
)

@REM The library offers no "no runfiles" signal; mirror its discovery inputs.
if not defined RUNFILES_DIR if not defined RUNFILES_MANIFEST_FILE if not exist "%~f0.runfiles\" if not exist "%~f0.runfiles_manifest" (
    echo Failed to locate runfiles >&2
    exit /b 2
)

:next_path
if "%~1"=="" exit /b 0
set "RESOLVED="
call :rlocation "%~1" RESOLVED
if errorlevel 1 (
    echo Failed to locate runfile: %~1 >&2
    exit /b 3
)
if not exist "%RESOLVED%" (
    echo Failed to locate runfile: %~1 >&2
    exit /b 3
)
type "%RESOLVED%"
shift
goto :next_path

@REM {RUNFILES_LIBRARY}
