if (-not $args[0]) {
    Write-Host "version is required for the release build" -ForegroundColor Red
    Write-Host "Usage: .\$($MyInvocation.MyCommand.Name) <version>"
    exit 1
}

$version = $args[0]

Write-Host "Run pre-build steps"
python tools/prebuild.py "v$version"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Pre-build steps failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Building version $version"
docker build . -t "littleorange666/book_manager:$version" --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Pushing version $version"
docker push "littleorange666/book_manager:$version"