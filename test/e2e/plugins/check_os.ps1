<#
    Nagios Plugin: Check Windows Version
    Returns the OS Caption and Build Version.
#>

try {
    # Fetch operating system details using CIM (modern replacement for WMI)
    $os = Get-CimInstance Win32_OperatingSystem
    
    $caption = $os.Caption
    $version = $os.Version
    $build   = $os.BuildNumber

    # Output text for Nagios (First line is the summary text)
    Write-Output "OK - Windows Version: $caption (Version $version, Build $build)"
    
    # Exit with Nagios OK status
    Exit 0
}
catch {
    Write-Output "UNKNOWN - Failed to retrieve Windows version: $_"
    Exit 3
}