@echo off
set PATH=%PATH%;C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin
cd build
MSBuild.exe performance_gateway.sln