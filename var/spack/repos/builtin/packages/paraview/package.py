##############################################################################
# Copyright (c) 2013-2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Spack.
# Created by Todd Gamblin, tgamblin@llnl.gov, All rights reserved.
# LLNL-CODE-647188
#
# For details, see https://github.com/spack/spack
# Please also see the NOTICE and LICENSE files for our notice and the LGPL.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License (as
# published by the Free Software Foundation) version 2.1, February 1999.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the terms and
# conditions of the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##############################################################################
from spack import *
import os


class Paraview(CMakePackage):
    """ParaView is an open-source, multi-platform data analysis and
    visualization application."""

    homepage = 'http://www.paraview.org'
    url      = "http://www.paraview.org/files/v5.3/ParaView-v5.3.0.tar.gz"
    _urlfmt  = 'http://www.paraview.org/files/v{0}/ParaView-v{1}{2}.tar.gz'

    version('5.4.1', '4030c70477ec5a85aa72d6fc86a30753')
    version('5.4.0', 'b92847605bac9036414b644f33cb7163')
    version('5.3.0', '68fbbbe733aa607ec13d1db1ab5eba71')
    version('5.2.0', '4570d1a2a183026adb65b73c7125b8b0')
    version('5.1.2', '44fb32fc8988fcdfbc216c9e40c3e925')
    version('5.0.1', 'fdf206113369746e2276b95b257d2c9b')
    version('4.4.0', 'fa1569857dd680ebb4d7ff89c2227378')

    variant('plugins', default=True,
            description='Install include files for plugins support')
    variant('python', default=False, description='Enable Python support')
    variant('mpi', default=True, description='Enable MPI support')
    variant('osmesa', default=False, description='Enable OSMesa support')
    variant('qt', default=False, description='Enable Qt (gui) support')
    variant('opengl2', default=True, description='Enable OpenGL2 backend')
    variant('examples', default=False, description="Build examples")
    variant('hdf5', default=False, description="Use external HDF5")

    depends_on('python@2:2.8', when='+python')
    depends_on('py-numpy', when='+python', type='run')
    depends_on('py-matplotlib', when='+python', type='run')
    depends_on('mpi', when='+mpi')
    depends_on('qt+opengl', when='@5.3.0:+qt+opengl2')
    depends_on('qt~opengl', when='@5.3.0:+qt~opengl2')
    depends_on('qt@:4', when='@:5.2.0+qt')

    depends_on('mesa+swrender', when='+osmesa')
    depends_on('libxt', when='+qt')
    conflicts('+qt', when='+osmesa')

    depends_on('bzip2')
    depends_on('freetype')
    # depends_on('hdf5+mpi', when='+mpi')
    # depends_on('hdf5~mpi', when='~mpi')
    depends_on('hdf5+hl+mpi', when='+hdf5+mpi')
    depends_on('hdf5+hl~mpi', when='+hdf5~mpi')
    depends_on('jpeg')
    depends_on('libpng')
    depends_on('libtiff')
    depends_on('libxml2')
    # depends_on('netcdf')
    # depends_on('netcdf-cxx')
    # depends_on('protobuf') # version mismatches?
    # depends_on('sqlite') # external version not supported
    depends_on('zlib')
    depends_on('cmake@3.3:', type='build')

    patch('stl-reader-pv440.patch', when='@4.4.0')

    # Broken gcc-detection - improved in 5.1.0, redundant later
    patch('gcc-compiler-pv501.patch', when='@:5.0.1')

    # Broken installation (ui_pqExportStateWizard.h) - fixed in 5.2.0
    patch('ui_pqExportStateWizard.patch', when='@:5.1.2')

    def url_for_version(self, version):
        """Handle ParaView version-based custom URLs."""
        if version < Version('5.1.0'):
            return self._urlfmt.format(version.up_to(2), version, '-source')
        else:
            return self._urlfmt.format(version.up_to(2), version, '')

    def setup_environment(self, spack_env, run_env):
        if os.path.isdir(self.prefix.lib64):
            lib_dir = self.prefix.lib64
        else:
            lib_dir = self.prefix.lib
        paraview_version = 'paraview-%s' % self.spec.version.up_to(2)
        run_env.prepend_path('LIBRARY_PATH', join_path(lib_dir,
                             paraview_version))
        run_env.prepend_path('LD_LIBRARY_PATH', join_path(lib_dir,
                             paraview_version))
        if '+python' in self.spec:
            run_env.prepend_path('PYTHONPATH', join_path(lib_dir,
                                 paraview_version))
            run_env.prepend_path('PYTHONPATH', join_path(lib_dir,
                                 paraview_version, 'site-packages'))
            run_env.prepend_path('PYTHONPATH', join_path(lib_dir,
                                 paraview_version, 'site-packages', 'vtk'))

    def cmake_args(self):
        """Populate cmake arguments for ParaView."""
        spec = self.spec

        def variant_bool(feature, on='ON', off='OFF'):
            """Ternary for spec variant to ON/OFF string"""
            if feature in spec:
                return on
            return off

        def nvariant_bool(feature):
            """Negated ternary for spec variant to OFF/ON string"""
            return variant_bool(feature, on='OFF', off='ON')

        rendering = variant_bool('+opengl2', 'OpenGL2', 'OpenGL')
        includes  = variant_bool('+plugins')

        cmake_args = [
            '-DPARAVIEW_BUILD_QT_GUI:BOOL=%s' % variant_bool('+qt'),
            '-DVTK_OPENGL_HAS_OSMESA:BOOL=%s' % variant_bool('+osmesa'),
            '-DVTK_USE_X:BOOL=%s' % nvariant_bool('+osmesa'),
            '-DVTK_RENDERING_BACKEND:STRING=%s' % rendering,
            '-DPARAVIEW_INSTALL_DEVELOPMENT_FILES:BOOL=%s' % includes,
            '-DBUILD_TESTING:BOOL=OFF',
            '-DBUILD_EXAMPLES:BOOL=%s' % variant_bool('+examples'),
            '-DVTK_USE_SYSTEM_FREETYPE:BOOL=ON',
            '-DVTK_USE_SYSTEM_HDF5:BOOL=%s' % variant_bool('+hdf5'),
            '-DVTK_USE_SYSTEM_JPEG:BOOL=ON',
            '-DVTK_USE_SYSTEM_LIBXML2:BOOL=ON',
            '-DVTK_USE_SYSTEM_NETCDF:BOOL=OFF',
            '-DVTK_USE_SYSTEM_TIFF:BOOL=ON',
            '-DVTK_USE_SYSTEM_ZLIB:BOOL=ON',
        ]

        # The assumed qt version changed to QT5 (as of paraview 5.2.1),
        # so explicitly specify which QT major version is actually being used
        if '+qt' in spec:
            cmake_args.extend([
                '-DPARAVIEW_QT_VERSION=%s' % spec['qt'].version[0],
            ])

        if '+python' in spec:
            cmake_args.extend([
                '-DPARAVIEW_ENABLE_PYTHON:BOOL=ON',
                '-DPYTHON_EXECUTABLE:FILEPATH=%s' % spec['python'].command.path
            ])

        if '+mpi' in spec:
            cmake_args.extend([
                '-DPARAVIEW_USE_MPI:BOOL=ON',
                '-DMPIEXEC:FILEPATH=%s/bin/mpiexec' % spec['mpi'].prefix,
                '-DMPI_CXX_COMPILER:PATH=%s' % spec['mpi'].mpicxx,
                '-DMPI_C_COMPILER:PATH=%s' % spec['mpi'].mpicc,
                '-DMPI_Fortran_COMPILER:PATH=%s' % spec['mpi'].mpifc
            ])

        if 'darwin' in spec.architecture:
            cmake_args.extend([
                '-DVTK_USE_X:BOOL=OFF',
                '-DPARAVIEW_DO_UNIX_STYLE_INSTALLS:BOOL=ON',
            ])

        # Hide git from Paraview so it will not use `git describe`
        # to find its own version number
        if spec.satisfies('@5.4.0:5.4.1'):
            cmake_args.extend([
                '-DGIT_EXECUTABLE=FALSE'
            ])

        return cmake_args
