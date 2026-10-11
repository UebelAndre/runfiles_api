# A small binary for accessing runfiles.
#
# Implements the subject contract in `CONTRIBUTING.md`. The runfiles module is
# inlined below so the script is self-contained; its class and functions are
# available to the rest of the script without `using module`.

# {RUNFILES_LIBRARY}

$ErrorActionPreference = 'Stop'

$EXIT_ERROR = 1
$EXIT_NO_RUNFILES = 2
$EXIT_NOT_FOUND = 3

# The subject is built in the main repository.
$SOURCE_REPO = ''

function Show-Usage {
    [Console]::Error.WriteLine('Usage: runfiles_user.ps1 [--bench ITERATIONS] <rlocationpath>...')
    [Console]::Error.WriteLine('Example: runfiles_user.ps1 workspace/path/to/file.txt')
}

$arguments = @($args)
$bench = $null
if ($arguments.Count -ge 2 -and $arguments[0] -eq '--bench') {
    $bench = [int]$arguments[1]
    $arguments = @($arguments | Select-Object -Skip 2)
}
if ($arguments.Count -eq 0) {
    Show-Usage
    exit $EXIT_ERROR
}

$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
try {
    $runfiles = [Runfiles]::Create($PSCommandPath, $SOURCE_REPO)
} catch {
    [Console]::Error.WriteLine("Failed to locate runfiles: $($_.Exception.Message)")
    exit $EXIT_NO_RUNFILES
}
$initNs = $stopwatch.Elapsed.Ticks * 100

if ($null -ne $bench) {
    $stopwatch.Restart()
    for ($i = 0; $i -lt $bench; $i++) {
        foreach ($path in $arguments) {
            $null = $runfiles.Rlocation($path)
        }
    }
    $lookupNs = $stopwatch.Elapsed.Ticks * 100
    Write-Output ('{{"init_ns":{0},"lookup_ns":{1},"iterations":{2},"paths":{3}}}' -f $initNs, $lookupNs, $bench, $arguments.Count)
    exit 0
}

foreach ($path in $arguments) {
    $resolved = $runfiles.Rlocation($path)
    if (-not $resolved -or -not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        [Console]::Error.WriteLine("Failed to locate runfile: $path")
        exit $EXIT_NOT_FOUND
    }
    [Console]::Out.Write([System.IO.File]::ReadAllText($resolved))
}
exit 0
