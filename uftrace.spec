# uftrace, especially on aarch64 is hurt by Fedora hardending flags:
%undefine        _fortify_level
%undefine        _hardened_build
%undefine        _include_frame_pointers
%undefine        _ld_as_needed
# https://github.com/namhyung/uftrace/issues/1343
%global          _lto_cflags %nil
%bcond_without   check
%bcond_without   python
Name:            uftrace
Version:         0.13.2
Release:         7%{?dist}

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
%global          have_pandoc 1
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
%make_install V=1

%check
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}
%{buildroot}%{_bindir}/uftrace --version
%{buildroot}%{_bindir}/uftrace record -A . -R . -P main ./uftrace
%{buildroot}%{_bindir}/uftrace replay
%{buildroot}%{_bindir}/uftrace dump
%{buildroot}%{_bindir}/uftrace info
%if %{with check}
unset CFLAGS CXXFLAGS LDFLAGS
make test V=1
%endif

%files
%{_bindir}/%{name}
%{_libdir}/libmcount*.so
# man pages needs pandoc, which plain centos and rhel don't have:
%if 0%{?have_pandoc}
%{_mandir}/man1/*.1*
%endif
%{_sysconfdir}/bash_completion.d/%{name}
%doc README.md
%license COPYING

%changelog
* Wed Mar 22 2023 Bernhard Kaindl <contact@bernhard.kaindl.dev> 0.13.2-7
- Initial rpm for Fedora/CentOS/EPEL
