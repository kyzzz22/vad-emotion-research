param(
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($PSScriptRoot)
$listener = $null

for ($candidate = $Port; $candidate -lt ($Port + 20); $candidate++) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $candidate)
        $listener.Start()
        $Port = $candidate
        break
    }
    catch {
        if ($listener) {
            $listener.Stop()
            $listener = $null
        }
    }
}

if (-not $listener) {
    throw "No available local port was found."
}

$mimeTypes = @{
    ".html" = "text/html; charset=utf-8"
    ".css"  = "text/css; charset=utf-8"
    ".js"   = "text/javascript; charset=utf-8"
    ".json" = "application/json; charset=utf-8"
    ".png"  = "image/png"
    ".svg"  = "image/svg+xml"
    ".ico"  = "image/x-icon"
}

$url = "http://127.0.0.1:$Port/"
Write-Host ""
Write-Host "VAD 3D demo is running:" -ForegroundColor Cyan
Write-Host $url -ForegroundColor Green
Write-Host "Keep this window open. Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

if (-not $NoBrowser) {
    Start-Process $url
}

try {
    while ($true) {
        $client = $listener.AcceptTcpClient()
        try {
            $stream = $client.GetStream()
            $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::ASCII, $false, 4096, $true)
            $requestLine = $reader.ReadLine()
            while ($reader.ReadLine()) { }

            if (-not $requestLine) {
                continue
            }

            $parts = $requestLine.Split(" ")
            $method = $parts[0]
            $requestPath = [System.Uri]::UnescapeDataString($parts[1].Split("?")[0])
            if ($requestPath -eq "/") {
                $requestPath = "/index.html"
            }

            $relativePath = $requestPath.TrimStart("/").Replace("/", [System.IO.Path]::DirectorySeparatorChar)
            $filePath = [System.IO.Path]::GetFullPath((Join-Path $root $relativePath))
            $allowed = $filePath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)

            if ($method -ne "GET" -or -not $allowed -or -not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
                $status = "404 Not Found"
                $body = [System.Text.Encoding]::UTF8.GetBytes("Not found")
                $contentType = "text/plain; charset=utf-8"
            }
            else {
                $status = "200 OK"
                $body = [System.IO.File]::ReadAllBytes($filePath)
                $extension = [System.IO.Path]::GetExtension($filePath).ToLowerInvariant()
                $contentType = $mimeTypes[$extension]
                if (-not $contentType) {
                    $contentType = "application/octet-stream"
                }
            }

            $headers = "HTTP/1.1 $status`r`nContent-Type: $contentType`r`nContent-Length: $($body.Length)`r`nCache-Control: no-cache`r`nConnection: close`r`n`r`n"
            $headerBytes = [System.Text.Encoding]::ASCII.GetBytes($headers)
            $stream.Write($headerBytes, 0, $headerBytes.Length)
            if ($method -eq "GET") {
                $stream.Write($body, 0, $body.Length)
            }
            $stream.Flush()
        }
        catch {
            Write-Warning $_.Exception.Message
        }
        finally {
            $client.Close()
        }
    }
}
finally {
    $listener.Stop()
}

