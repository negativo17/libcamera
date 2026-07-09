Name:    libcamera
Epoch:   1
Version: 0.7.1
Release: 7%{?dist}
Summary: A library to support complex camera ISPs
# see .reuse/dep5 and COPYING for details
License: LGPL-2.1-or-later
URL:     http://libcamera.org/

Source0: https://gitlab.freedesktop.org/camera/libcamera/-/archive/v%{version}/%{name}-v%{version}.tar.bz2
Source1: qcam.desktop
Source2: qcam.metainfo.xml
Source3: 70-libcamera.rules

Patch01: 0001-disable-rpi-pisp.patch
# Expose Intel IPU cameras through the proprietary libcamhal HAL (full Intel
# imaging) instead of the software ISP. See the patch header for details.
# The default "auto" pipeline set now includes the "libcamhal" handler.
# At runtime "simple" detects libcamhal and yields Intel IPU devices to it, so
# the IPU camera is exposed only through the HAL (full Intel imaging) while the
# software-ISP path stays available for everything else.
Patch02: 0002-add-libcamhal-pipeline-handler.patch

# libcamera does not currently build on these architectures
ExcludeArch: s390x ppc64le

BuildRequires: gcc-c++
# Headers for the libcamhal pipeline handler
%ifarch x86_64
BuildRequires: libcamhal-devel
%endif
BuildRequires: gtest-devel
BuildRequires: desktop-file-utils
BuildRequires: meson
BuildRequires: openssl
BuildRequires: ninja-build
BuildRequires: pkgconfig(glib-2.0)
BuildRequires: gnutls-devel
BuildRequires: pkgconfig(gstreamer-video-1.0)
BuildRequires: pkgconfig(gstreamer-allocators-1.0)
BuildRequires: libatomic
BuildRequires: pkgconfig(libdw)
BuildRequires: libevent-devel
BuildRequires: libjpeg-turbo-devel
BuildRequires: libtiff-devel
BuildRequires: libyaml-devel
BuildRequires: libyuv-devel
BuildRequires: lttng-ust-devel
BuildRequires: pkgconfig(Qt6Core)
BuildRequires: pkgconfig(Qt6Gui)
BuildRequires: pkgconfig(Qt6OpenGL)
BuildRequires: pkgconfig(Qt6OpenGLWidgets)
BuildRequires: pkgconfig(Qt6Widgets)
BuildRequires: pybind11-devel
BuildRequires: python3-devel
BuildRequires: python3-jinja2
BuildRequires: python3-ply
BuildRequires: python3-pyyaml
BuildRequires: SDL2-devel
BuildRequires: systemd-devel
# libcamera is not really usable without its IPA plugins
Recommends: %{name}-ipa%{?_isa}
# The libcamhal pipeline handler dlopen()s this at runtime; it is also used by
# the "simple" handler to detect the HAL and yield Intel IPU devices to it.
%ifarch x86_64
Requires: libcamhal
%endif

Obsoletes: libcamera-doc < 0.6.0

%description
libcamera is a library that deals with heavy hardware image processing
operations of complex camera devices that are shared between the linux
host all while allowing offload of certain aspects to the control of
complex camera hardware such as ISPs.

Hardware support includes USB UVC cameras, libv4l cameras as well as more
complex ISPs (Image Signal Processor).

%package     devel
Summary:     Development package for %{name}
Requires:    %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description devel
Files for development with %{name}.

%package     ipa
Summary:     ISP Image Processing Algorithm Plugins for %{name}
License:     LGPL-2.1-or-later AND BSD-2-Clause
Requires:    %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description ipa
Image Processing Algorithms plugins for interfacing with device
ISPs for %{name}

%package     tools
Summary:     Tools for %{name}
License:     LGPL-2.1-or-later AND BSD-3-Clause
Requires:    %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description tools
Command line tools for %{name}

%package     qcam
Summary:     Graphical QCam application for %{name}
License:     GPL-2.0-or-later AND MIT
Requires:    %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description qcam
Graphical QCam application for %{name}

%package     gstreamer
Summary:     GSTreamer plugin for %{name}
Requires:    %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description gstreamer
GSTreamer plugins for %{name}

%package     v4l2
Summary:     V4L2 compatibility layer for %{name}
Requires:    %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description v4l2
V4L2 compatibility layer for %{name}

%package     -n python3-%{name}
Summary:     Python bindings for %{name}
Requires:    %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description -n python3-%{name}
Python bindings for %{name}

%prep
%autosetup -p1 -n %{name}-v%{version}

%build
export CFLAGS="%{optflags} -Wno-deprecated-declarations"
# Set also max-devirt-targets=1 to prevent compilation errors,
# maybe due to https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120345.
export CXXFLAGS="%{optflags} -Wno-deprecated-declarations --param=max-devirt-targets=1"

# Build and include the virtual and vimc pipelines. This also builds tests but
# those do not get included in any packages.
%meson \
    -Dv4l2=enabled \
    -Dlc-compliance=disabled \
    -Dlibunwind=disabled \
    -Dtest=true \
    -Ddocumentation=disabled \
    -Drpi-awb-nn=disabled \
    %{nil}
%meson_build

# Stripping requires the re-signing of IPA libraries, manually
# copy standard definition of __spec_install_post and re-sign.
%define __spec_install_post \
    %{?__debug_package:%{__debug_install_post}} \
    %{__arch_install_post} \
    %{__os_install_post} \
    %{_builddir}/%{name}-v%{version}/src/ipa/ipa-sign-install.sh %{_builddir}/%{name}-v%{version}/%{_vpath_builddir}/src/ipa-priv-key.pem %{buildroot}/%{_libdir}/libcamera/ipa_*.so \
%{nil}

%install
%meson_install

# Install Desktop Entry file
desktop-file-install --dir=%{buildroot}%{_datadir}/applications \
                     %SOURCE1

# Install AppStream metainfo file
mkdir -p %{buildroot}/%{_metainfodir}/
cp -a %SOURCE2 %{buildroot}/%{_metainfodir}/

# Install udev rules
mkdir -p %{buildroot}/%{_udevrulesdir}/
install -D -m 644 %SOURCE3 %{buildroot}/%{_udevrulesdir}/

%files
%license COPYING.rst LICENSES/LGPL-2.1-or-later.txt
# We leave the version here explicitly to know when it bumps
%{_libdir}/libcamera*.so.0.7
%{_libdir}/libcamera*.so.%{version}
%{_udevrulesdir}/70-libcamera.rules

%files devel
%{_includedir}/%{name}/
%{_libdir}/libcamera*.so
%{_libdir}/pkgconfig/libcamera-base.pc
%{_libdir}/pkgconfig/libcamera.pc

%files ipa
%{_datadir}/libcamera/
%{_libdir}/libcamera/
%{_libexecdir}/libcamera/
%exclude %{_libexecdir}/libcamera/v4l2-compat.so

%files gstreamer
%{_libdir}/gstreamer-1.0/libgstlibcamera.so

%files qcam
%{_bindir}/qcam
%{_datadir}/applications/qcam.desktop
%{_metainfodir}/qcam.metainfo.xml

%files tools
%license LICENSES/GPL-2.0-only.txt
%{_bindir}/cam
%{_bindir}/libcamera-bug-report

%files v4l2
%{_bindir}/libcamerify
%{_libexecdir}/libcamera/v4l2-compat.so

%files -n python3-%{name}
%{python3_sitearch}/*

%changelog
* Thu Jul 09 2026 negativo17 <build@negativo17.org> - 1:0.7.1-7
- Add libcamhal pipeline handler for Intel IPU (IPU6/IPU7/IPU8) cameras.
- Have the "simple" software-ISP handler detect libcamhal at runtime and yield
  Intel IPU devices to the HAL, so the IPU camera is exposed only through
  libcamhal (full Intel imaging) with no software-ISP duplicate.
- Bump Epoch to 1.

* Fri Jun 12 2026 Yaakov Selkowitz <yselkowi@redhat.com> - 0.7.1-6
- Rebuilt for openssl 4.0

* Fri Jun 05 2026 Python Maint <python-maint@redhat.com> - 0.7.1-5
- Rebuilt for Python 3.15

* Thu Jun 04 2026 Milan Zamazal <mzamazal@redhat.com> - 0.7.1-4
- Don't disable LTO

* Wed Jun 03 2026 Python Maint <python-maint@redhat.com> - 0.7.1-3
- Rebuilt for Python 3.15

* Mon May 18 2026 Yaakov Selkowitz <yselkowi@redhat.com> - 0.7.1-2
- Use libdw for backtraces

* Fri May 01 2026 Milan Zamazal <mzamazal@redhat.com> - 0.7.1-1
- Update to version 0.7.1
- New libcamera-bug-report utility added to tools

* Thu Jan 29 2026 Milan Zamazal <mzamazal@redhat.com> - 0.7.0-1
- Update to version 0.7.0

* Fri Jan 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild
