<#
    choco_prereqs_ci.ps1

    Slim CI/self-hosted runner variant of choco_prereqs.ps1.
    Skips Visual Studio, Perl, NASM, and Python installs that are
    expected to already be present on GitHub Actions runners or a
    pre-provisioned self-hosted machine.
#>

& "$PSScriptRoot\choco_prereqs.ps1" -CI @args
