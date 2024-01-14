$pts = Get-ChildItem | Where-Object { $_.PSIsContainer }

foreach ($pt in $pts)
{
    Write-Output "Anonymising DICOM folder $pt..."
    Start-Process -FilePath dicom_anon.bat -ArgumentList $pt -NoNewWindow -Wait
}