@echo off
rem calamity: run the Calamity engine from anywhere (Windows). The learner's repository is %CALAMITY_ROOT%,
rem else the plugin's learner_dir setting, else the current folder unless it is this framework copy (a clone).
setlocal
set "HERE=%~dp0.."
for %%I in ("%HERE%") do set "HERE=%%~fI"
if not defined CALAMITY_ROOT if defined CLAUDE_PLUGIN_OPTION_LEARNER_DIR set "CALAMITY_ROOT=%CLAUDE_PLUGIN_OPTION_LEARNER_DIR%"
if not defined CALAMITY_ROOT if /i not "%CD%"=="%HERE%" set "CALAMITY_ROOT=%CD%"
where python >nul 2>nul && (python "%HERE%\engine\calamity.py" %* & exit /b) 
py -3 "%HERE%\engine\calamity.py" %*
