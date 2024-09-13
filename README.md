# Reactor-Neutronics-Simulation-Plotting

This repository runs a neutronics simulation with OpenMC using a makeshift simplified spherical reactor and plots the results of the simulation. A detailed README is attached in the repository labeled README.docx explaining how the code works and how to make changes to it.

# Installation

OpenMC must first be installed on your computer. OpenMC is an open source Monte Carlo neutronics simulation Python package geared towards Linux users; however, OpenMC's website lists some possible ways to install this package on Mac and Windows as well: https://docs.openmc.org/en/latest/quickinstall.html

Issues may arise when trying to follow their various installation methods. For example, with Conda, the OpenMC repository might not even show up. With Docker, pulling the OpenMC Docker Image (openmc/openmc) may give an error if no matching manifest for linux/arm64/v8 is found. With Source, you may need to continuously install various files and other libraries, and an inexperience in working with manual installations may make this process take a very long time and/or have you accidentally delete or uninstall files you don't actually want removed from your computer.

Another option is to acquire a paid paperspace linux machine (https://www.paperspace.com/machines) and work remotely via ssh on a Linux machine, installing OpenMC on the machine instead of your personal computer. OpenMC runs perfectly well on a SPARTA Ubuntu 20.04 machine.
