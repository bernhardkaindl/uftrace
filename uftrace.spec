# https://github.com/namhyung/uftrace/issues/1343
%global          _lto_cflags %nil
%bcond_without   check
%bcond_with      python
Name:            uftrace
Version:         0.13.2
Release:         3%{?dist}

Summary:         Function (graph) tracer for user-space

License:         GPL-2.0
Group:           Development/Debuggers
Url:             https://github.com/bernhardkaindl/uftrace
Source:          %{name}-%{version}.tar.gz

ExclusiveArch:   x86_64 %ix86 aarch64

BuildRequires:   elfutils-devel
%if "%{?toolchain}" == "clang"
BuildRequires:   clang compiler-rt
%else
BuildRequires:   gcc-c++
%endif
BuildRequires:   libstdc++-devel
BuildRequires:   make
BuildRequires:   ncurses-devel
%if 0%{?centos} > 8 || 0%{?rhel} > 8 || 0%{?fedora} > 35
BuildRequires:   capstone-devel
%endif
%if 0%{?fedora} > 35
BuildRequires:   luajit-devel
BuildRequires:   libunwind-devel
BuildRequires:   pandoc
%endif
%if %{with python}
BuildRequires:   python3-devel
%else
BuildRequires:   python3
%endif
%if %{with check}
# segfaults without /proc
BuildRequires:   /proc
%endif

%description
The uftrace tool is to trace and analyze execution of a program written in
C/C++. It was heavily inspired by the ftrace framework of the Linux kernel
(especially function graph tracer) and supports userspace programs. It supports
various kind of commands and filters to help analysis of the program execution
and performance.

%prep
%setup -q
# build only tests
sed -i 's|test_unit|unittest|' Makefile
sed -i 's|python$|python3|' tests/runtest.py

%build
# uftrace is hurt by hardending flags:
%undefine        _hardened_build
%undefine        _fortify_level
%undefine        _ld_as_needed
%undefine        _include_frame_pointers
%ifarch aarch64
%undefine        optflags
%endif
env | grep FLAGS
unset CFLAGS CXXFLAGS LDFLAGS
%if %{without python}
conf_flags="--without-libpython"
%endif
./configure --prefix=%{_prefix} --libdir=%{_libdir} $conf_flags
%make_build
%if %{with check}
# build only here
%make_build unittest
%endif

%install
unset CFLAGS CXXFLAGS LDFLAGS
%make_install V=1

%check
unset CFLAGS CXXFLAGS LDFLAGS
./uftrace --version
LD_LIBRARY_PATH=$PWD/libmcount ./uftrace record -A . -R . -P main ./uftrace
./uftrace replay
./uftrace dump
./uftrace info
%if %{with check}
set -v
make test V=1
%endif

%files
%{_bindir}/%{name}
%{_libdir}/libmcount*.so
%if %{with python}
%{_libdir}/uftrace_python.so
%{_libdir}/uftrace.py
%endif
# man pages needs pandoc, which plain centos and rhel don't have:
%if 0%{?fedora} > 35
%{_mandir}/man1/*.1*
%endif
%{_sysconfdir}/bash_completion.d/%{name}
%doc README.md
%license COPYING

%changelog
* Mon Mar 20 2023 Bernhard Kaindl <contact@bernhard.kaindl.dev> 0.13-0
- Initial rpm for Fedora/CentOS/EPEL
