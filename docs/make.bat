@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=uv run --extra dev sphinx-build
)
if "%STAGEDBUILD%" == "" (
	set STAGEDBUILD=uv run --extra dev python _scripts/build_versioned_docs.py
)
set SOURCEDIR=.
set BUILDDIR=build

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The documentation build command was not found. Make sure you have uv
	echo.installed, or set the SPHINXBUILD environment variable to point to a
	echo.working Sphinx command. Alternatively you may add the required
	echo.executables to PATH.
	echo.
	echo.If you don't have uv installed, grab it from
	echo.https://docs.astral.sh/uv/
	exit /b 1
)

if "%1" == "" goto help
if /I "%1" == "help" goto help
if /I "%1" == "clean" goto clean

%STAGEDBUILD% --builder %1 "%BUILDDIR%\%1" %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:clean
if exist "%BUILDDIR%" rmdir /s /q "%BUILDDIR%"

:end
popd
