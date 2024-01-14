@echo off 
Rem Select dicom folder and anonymise
REM: Argument: folder

REM: print new line
echo.

set current_folder=%1
set anon_folder=%current_folder%_anon

REM: Make new folder to contain the anonymised info
md %anon_folder%

echo Creating %anon_folder% from %current_folder%:
echo.

dicom-anonymizer %current_folder% %anon_folder% -t "(0x0008, 0x103E)" keep -t "(0x0010, 0x0010)" "regexp" "[\s\S]+" %current_folder% -t "(0x0010, 0x0020)" "regexp" "[\s\S]+" %current_folder% --keepPrivateTags

echo.
