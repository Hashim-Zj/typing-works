<#
Windows PowerShell launcher for the Typing Test project.
Usage: .\start.ps1 --help
#>
param(
    [Parameter(Position = 0)]
    [string]$Command = "--setup",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$TestArgs
)

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

function Show-Help {
@"
Typing Test launcher

Usage:
  .\run.ps1 [command] [options]

With no command, a guided setup asks for each test option step by step.

Commands:
  terminal [--time SECONDS|unlimited | --words COUNT|unlimited]
           [--content words|numbers|punctuation|mixed] [--capitalization lower|capitalized|random]
           [--custom-text "TEXT"]
      Start the interactive terminal typing test. Default: 60 seconds.
      Esc or Ctrl+C saves current progress and exits. Enter inserts a newline.
      Examples: .\run.ps1 terminal --time 30 --content mixed --capitalization random
                .\run.ps1 terminal --words unlimited --content numbers

  history
      Show saved terminal WPM and accuracy graphs plus recent results.

  web [PORT]
      Serve the browser typing test at http://localhost:PORT.
      Default port: 8000. Stop the server with Ctrl+C.
      Example: .\run.ps1 web 8080

  help, --help, -h
      Show this help text.

The browser test has all content modes, custom text, unlimited modes, live
WPM graphs, and browser-saved history. Terminal results are saved in
data\typing_results.json.
"@ | Write-Output
}

switch ($Command.ToLowerInvariant()) {
    "--setup" {
        & python typing_test.py --setup
        exit $LASTEXITCODE
    }
    "terminal" {
        & python typing_test.py @TestArgs
        exit $LASTEXITCODE
    }
    "history" {
        & python typing_test.py --history
        exit $LASTEXITCODE
    }
    "web" {
        $Port = if ($TestArgs.Count -gt 0) { $TestArgs[0] } else { "8000" }
        $PortNumber = 0
        if (-not [int]::TryParse($Port, [ref]$PortNumber) -or $PortNumber -lt 1 -or $PortNumber -gt 65535) {
            Write-Error "Port must be a number from 1 to 65535."
            exit 2
        }
        Write-Output "Browser test: http://localhost:$PortNumber"
        Write-Output "Press Ctrl+C to stop the web server."
        & python -m http.server $PortNumber --directory web
        exit $LASTEXITCODE
    }
    { $_ -in "help", "--help", "-h" } { Show-Help }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 2
    }
}
