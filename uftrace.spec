%bcond_without   check
%bcond_without   python
Name:            uftrace
Version:         0.13
Release:         11%{?dist}

Summary:         Function graph tracer for C/C++/Rust with many features
# https://github.com/namhyung/uftrace/issues/1343
%global          _lto_cflags %nil
# These flags cause bugs (detected by the test suite):
%undefine        _fortify_level
%undefine        _hardened_build
%undefine        _include_frame_pointers

License:         GPL-2.0
Url:             https://github.com/namhyung/uftrace
Source:          https://github.com/namhyung/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz

ExclusiveArch:   x86_64 %ix86 %arm aarch64

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
C/C++/Rust. It was heavily inspired by the ftrace framework of the Linux kernel
(especially function graph tracer) and supports userspace programs. It supports
various kind of commands and filters to help analysis of the program execution
and performance.

%prep
%setup -q
# build only tests
sed -i 's|test_unit|unittest|' Makefile
sed -i 's|python$|python3|' tests/runtest.py
rm tests/t151_recv_runcmd.py # Fixed in git but can cause trouble in 0.13

%build
%if %{without python}
conf_flags="--without-libpython"
%endif
%configure $conf_flags
%make_build
%if %{with check}
# build only here
%make_build unittest
%endif

%install
%make_install V=1
%if %{with check}
unset CFLAGS CXXFLAGS LDFLAGS
make test V=1 >test-report.txt 2>&1 &
TEST=$?
tail -f test-report.txt &
wait $TEST
%endif

cd %{buildroot}
mkdir -p                             .%{_datadir}/bash_completion
mv .%{_sysconfdir}/bash_completion.d .%{_datadir}/bash_completion/completions

%check
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}
%{buildroot}%{_bindir}/uftrace --version
%{buildroot}%{_bindir}/uftrace record -A . -R . -P main ./uftrace
%{buildroot}%{_bindir}/uftrace replay
%{buildroot}%{_bindir}/uftrace dump
%{buildroot}%{_bindir}/uftrace info

%files
%{_bindir}/%{name}
%{_libdir}/libmcount*.so
# man pages needs pandoc, which plain centos and rhel don't have:
%if 0%{?have_pandoc}
%{_mandir}/man1/*.1*
%endif
%{_datadir}/bash_completion/completions/%{name}
%doc README.md test-report.txt
%license COPYING

%changelog
* Wed Mar 22 2023 Bernhard Kaindl <contact@bernhard.kaindl.dev> 0.13-10
- Initial rpm for Fedora and CentOS Stream
