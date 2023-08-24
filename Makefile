# See the README.md notes on how to use this Makefile - for advanced usage only

#
SHELL = /bin/bash

#
TIME = /usr/bin/time

# use python3 or anaconda3
PYTHON = anaconda3

# git directories we should have here

GIT_DIRS = athenak

# URLs that we'll need

URL2  = https://github.com/teuben/Athena-miniK
URL3  = https://github.com/teuben/nemo

# the ATHENA executable

ATHENA = athenak/build/src/athena

.PHONY:  help install build


install: help
	@echo "These are some make targets we advertise. See Makefile for details"

help:
## help:          This Help
help : Makefile
	@sed -n 's/^##//p' $<


## git:           Get all git repos for this install
git:  $(GIT_DIRS)

## pull:          Update all git repos
pull:
	git pull
	-@for dir in $(GIT_DIRS); do\
	(echo -n "$$dir: " ;cd $$dir; git pull); done

status:
	@echo -n "lmtoy: "; git status -uno
	-@for dir in $(GIT_DIRS); do\
	(echo -n "$$dir: " ;cd $$dir; git status -uno); done

athenak:
	git clone --recursive $(URL2) athenak

nemo:
	git clone $(URL3)

python: nemo anaconda3

anaconda3:
	nemo/src/scripts/install_anaconda3


## build_athenak:  generic build athenak
build_athenak:	athenak
	(mkdir -p athenak/build; cd athenak/build; cmake ..; make -j 8)

## arm:            build for mac-M1 arm architecture (use ARM= to override defaults)
# See also:   https://kokkos.github.io/kokkos-core-wiki/keywords.html#keywords-arch
ARM = -D CMAKE_CXX_COMPILER=clang++-mp-15 -D CMAKE_C_COMPILER=clang-mp-15 -D Kokkos_ARCH_ARMV81=On
arm:	athenak
	(mkdir -p athenak/build; cd athenak/build; cmake $(B_ARM) ..; make -j 8)

#PJT =  -D CMAKE_CXX_COMPILER=clang++ -D CMAKE_C_COMPILER=clang -D Kokkos_ARCH_INTEL_DG1=On
#PJT =  -D Kokkos_ARCH_INTEL_DG1=On
PJT =  -D Kokkos_ENABLE_OPENMP=On
#PJT =  -D Athena_ENABLE_MPI=ON
pjt:	athenak
	(mkdir -p athenak/build; cd athenak/build; cmake $(PJT) ..; make -j 8)

## build_python:    build your private anaconda3:     source anaconda3/python_start.sh
build_python:  python

# a few sample benchmark runs

##

## run1:          benchmark 1D linear_wave_hydro (athenak)   [ < 1sec  1069 cycles]
run1:
	$(TIME) $(ATHENA) -i athenak/inputs/linear_wave_hydro.athinput -d run1
	@echo ./animate1 base=run1/tab/LinWave xcol=x1v ycol=velx

## run2:          benchmark 2D orszag_tang (athenak) [ ~109"  1403 cycles]
run2:
	$(TIME) $(ATHENA) -i athenak/inputs/orszag_tang.athinput      -d run2
	@echo ./animate1 base=run2/tab/Advect xcol=x1v ycol=dens



## 


## test1:         new pyThena
test1:
	./pythena.py

