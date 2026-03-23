@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=uv run --extra dev sphinx-build
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

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd
