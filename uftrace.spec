%bcond_without   check
%bcond_without   python
Name:            uftrace
Version:         0.13
Release:         12%{?dist}

Summary:         Function graph tracer for C and C++ with many features
# https://github.com/namhyung/uftrace/issues/1343
%global          _lto_cflags %nil
# -fPIE/-fpie is not supported for building uftrace and forcing it causes test regressions:
%undefine        _hardened_build
License:         GPL-2.0
Url:             https://github.com/namhyung/uftrace
Source:          https://github.com/namhyung/%{name}/archive/v%{version}/%{name}-%{version}.tar.gz

ExclusiveArch:   x86_64 %ix86 %arm aarch64

BuildRequires:   elfutils-devel
%if %{with check}
BuildRequires:   clang compiler-rt
BuildRequires:   /proc
%endif
BuildRequires:   gcc-c++
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

%description
uftrace is a function call graph tracer for programs, optionally including nested
library calls and even seamless function graph tracing of used kernel functions.

- The output is shows colored nested function call graphs (instead of listings)
- Parsing and formatting of all funtion arguments using libc function prototypes
  and DWARF debug information values is supported as well
- It has rich filters such as filtering by function call duration for analysis
  of program execution and performance
- It includes trace kernel events such as kernel scheduling events affecting
  the execution timing in the trace and records nanosecond-exact timestamps
  
%prep
%setup -q
cd tests
sed -i 's|python$|python3|' runtest.py
rm *pmu_*.py t140_dynamic_xray.py           # These don't PASS cloud VMs without PMU access.
rm t014_ucontext.py *taskname*.py *sched.py # Kernel API access dependency
%ifarch x86_64
rm t212_noplt_libcall.py *_report_* t121_malloc_fork.py # Diff, To be fixed
rm t220_trace_script.py  # Very long output diff on native FC37 install
%endif
%ifarch aarch64
rm *_retval.py  *float*.py *nested_func*.py *signal* # Different ouput, to be fixed
%endif
rm *replay*.py *exception*.py # To be fixed, Differs between gcc and clang
rm t200_lib_dlopen2.py t151_recv_runcmd.py t219_no_libcall_script.py *_arg*.py # To be fixed in v0.14
# Timing/races:
rm t035_filter_demangle[135].py t135_trigger_time2.py
rm t223_dynamic_full.py        t226_default_opts.py
%ifarch x86_64
rm t049_column_view.py t118_thread_tsd.py t217_no_libcall_dump.py
rm t033_filter_demangle3.py  # Mssing b() {
rm t172_trigger_filter.py    # Missing ns::ns1::foo::foo();
rm t181_graph_full.py        # simple tree node output ordering issue
rm t191_posix_spawn.py # Sometimes has nonzero output status
%endif
rm t273_agent_basic.py # Sometimes has nonzero output status
%ifarch aarch64
# rm *no_libcall*.py *dynamic_xray.py   # Kernel API access dependency
# Seem to be timing-dependent on fc38-aarch64-ampere-a1:
rm t071_graph_depth.py t102_dump_flamegraph.py t208_watch_cpu.py
%if 0%{?centos} >= 8 || 0%{?fedora} >= 38
rm *_no_libcall_*.py # Fail to compile their testcases
rm t168_lib_nested.py t192_lib_name.py # Abnormal exit by signal
%endif
%endif

%build
%if %{without python}
conf_flags="--without-libpython"
%endif
%if "%{version}" == "0.13"
# Fix incorrect floating point argument/return values:
# https://github.com/namhyung/uftrace/issues/1631 https://github.com/namhyung/uftrace/pull/1632
%ifarch x86_64
CFLAGS="$CFLAGS -fno-builtin -fno-tree-vectorize"
%endif
%endif
%configure --libdir=%{_libdir}/%{name} $conf_flags
%make_build
%if %{with check}
%make_build unittest
%endif

%install
make install DESTDIR=%{buildroot} V=1
%if %{with check}
# Builds all test programs with all gcc and clang and -O0, -Os, -O1, -O2, -O3,
# and the tracing output it needs to be identical. Other CFLAGS cause diffs(fails).
# The test report is packaged, checked again and shown at the end of check:
unset CFLAGS CXXFLAGS LDFLAGS
# On aarch64, clang has fewer quirks, giving more focussed test results:
make runtest WORKER="--keep --diff -O2" >test-report.txt 2>&1 &
TEST=$!
sleep 1
stdbuf -oL tail -f test-report.txt &
wait $TEST
%endif

cd %{buildroot}
mkdir -p                             .%{_datadir}/bash_completion
mv .%{_sysconfdir}/bash_completion.d .%{_datadir}/bash_completion/completions

%check
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}/%{name}
%{buildroot}%{_bindir}/uftrace --version
%{buildroot}%{_bindir}/uftrace record -A . -R . -P main ./uftrace
%{buildroot}%{_bindir}/uftrace replay
%{buildroot}%{_bindir}/uftrace dump
%{buildroot}%{_bindir}/uftrace info
# Show and check the test report. Fail the build on any regression:
tail -12 test-report.txt
tail -12 test-report.txt |
   while read sym count text;do
      case "$text" in
         "Different test result")   test $count -le   2;; # t226_default_opts/gcc/aarch
         "Test succeeded (with"*)   test $count -ge   8;;
%ifarch aarch64
         "Test succeeded")          test $count -ge 616;; # Due to signals/races/FC38
         "Build failed")            test $count -le  12;;
%endif
%ifarch x86_64
         "Test succeeded")          test $count -ge 364;; # Due to signals/races/FC38
         "Build failed")            test $count -le 189;;
%endif
         "Skipped")                 test $count -le  70;; # centos-9-aarch64-ampere-a1
         "Non-zero return value")   test $count -le   0;; # Rawhide/FC38!
         "Abnormal exit by signal") test $count -le   8;; # Rawhide/FC38!
      esac
   done

%files
%{_bindir}/%{name}
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/libmcount*.so
%if 0%{?have_pandoc}
%{_mandir}/man1/*.1*
%endif
%{_datadir}/bash_completion/completions/%{name}
%doc README.md test-report.txt
%license COPYING

%changelog
* Fri Mar 24 2023 Bernhard Kaindl <contact@bernhard.kaindl.dev> 0.13-12
- Initial rpm for Fedora and CentOS Stream
