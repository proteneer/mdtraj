import numpy as np
import tempfile
import os
from mdtraj import hdf5
from mdtraj import HDF5TrajectoryFile
from mdtraj.testing import get_fn, eq, DocStringFormatTester, raises, skipif, assert_raises
# DocStringTester = DocStringFormatTester(hdf5)

try:
    import simtk.unit as units
    HAVE_UNITS = True
except ImportError:
    HAVE_UNITS = False

temp = tempfile.mkstemp(suffix='.h5')[1]
def teardown_module(module):
    """remove the temporary file created by tests in this file
    this gets automatically called by nose"""
    os.unlink(temp)


def test_write_coordinates():
    coordinates = np.random.randn(4, 10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates)

    with HDF5TrajectoryFile(temp) as f:
        yield lambda: eq(f.root.coordinates[:], coordinates)
        yield lambda: eq(str(f.root.coordinates.attrs['units']), 'nanometers')


def test_write_coordinates_reshape():
    coordinates = np.random.randn(10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates)

    with HDF5TrajectoryFile(temp) as f:
        yield lambda: eq(f.root.coordinates[:], coordinates.reshape(1,10,3))
        yield lambda: eq(str(f.root.coordinates.attrs['units']), 'nanometers')


def test_write_multiple():
    coordinates = np.random.randn(4, 10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates)
        f.write(coordinates)

    with HDF5TrajectoryFile(temp) as f:
        yield lambda: eq(f.root.coordinates[:], np.vstack((coordinates, coordinates)))


def test_write_inconsistent():
    coordinates = np.random.randn(4, 10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates)
        with assert_raises(ValueError):
            # since the first frames we saved didn't contain velocities, we
            # can't save more velocities
            f.write(coordinates, velocities=coordinates)


def test_write_inconsistent_2():
    coordinates = np.random.randn(4, 10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates, velocities=coordinates)
        with assert_raises(ValueError):
            # we're saving a deficient set of data, since before we wrote
            # more information.
            f.write(coordinates)


@skipif(not HAVE_UNITS, 'No units')
def test_write_units():
    "simtk.units are automatically converted into MD units for storage on disk"
    coordinates = units.Quantity(np.random.randn(4, 10,3), units.angstroms)
    velocities = units.Quantity(np.random.randn(4, 10,3), units.angstroms/units.year)

    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates, velocities=velocities)

    with HDF5TrajectoryFile(temp) as f:
        yield lambda: eq(f.root.coordinates[:], coordinates.value_in_unit(units.nanometers))
        yield lambda: eq(str(f.root.coordinates.attrs['units']), 'nanometers')

        yield lambda: eq(f.root.velocities[:], velocities.value_in_unit(units.nanometers/units.picosecond))
        yield lambda: eq(str(f.root.velocities.attrs['units']), 'nanometers/picosecond')


@skipif(not HAVE_UNITS, 'No units')
def test_write_units_mismatch():
    velocoties = units.Quantity(np.random.randn(4, 10,3), units.angstroms/units.picosecond)

    with HDF5TrajectoryFile(temp, 'w') as f:
        with assert_raises(TypeError):
            # if you try to write coordinates that are unitted and not
            # in the correct units, we find that
            f.write(coordinates=velocoties)


def test_topology():
    from mdtraj import trajectory, topology
    top = trajectory.load_pdb(get_fn('native.pdb')).topology

    with HDF5TrajectoryFile(temp, 'w') as f:
        f.topology = top

    with HDF5TrajectoryFile(temp) as f:
        assert f.topology == top


def test_constraints():
    c = np.array([(1,2,3.5)], dtype=np.dtype([('atom1', np.int32), ('atom2', np.int32), ('distance', np.float32)]))

    with HDF5TrajectoryFile(temp, 'w') as f:
        f.constraints = c

    with HDF5TrajectoryFile(temp) as f:
        yield lambda: eq(f.constraints, c)


def test_constraints2():
    c = np.array([(1,2,3.5)], dtype=np.dtype([('atom1', np.int32), ('atom2', np.int32), ('distance', np.float32)]))

    with HDF5TrajectoryFile(temp, 'w') as f:
        f.constraints = c
        f.constraints = c

    with HDF5TrajectoryFile(temp) as f:
        yield lambda: eq(f.constraints, c)
def test_read_0():
    coordinates = np.random.randn(4, 10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates, alchemicalLambda=np.array([1,2,3,4]))

    with HDF5TrajectoryFile(temp) as f:
        got = f.read()
        yield lambda: eq(got.coordinates, coordinates)
        yield lambda: eq(got.velocities, None)
        yield lambda: eq(got.alchemicalLambda, np.array([1,2,3,4]))


@np.testing.decorators.skipif(not HAVE_UNITS)
def test_read_1():
    coordinates = units.Quantity(np.random.randn(4, 10,3), units.angstroms)
    velocities = units.Quantity(np.random.randn(4, 10,3), units.angstroms/units.years)


    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates, velocities=velocities)

    with HDF5TrajectoryFile(temp) as f:
        got = f.read()
        yield lambda: eq(got.coordinates, coordinates.value_in_unit(units.nanometers))
        yield lambda: eq(got.velocities, velocities.value_in_unit(units.nanometers/units.picoseconds))


def test_read_slice_0():
    coordinates = np.random.randn(4, 10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates, alchemicalLambda=np.array([1,2,3,4]))

    with HDF5TrajectoryFile(temp) as f:
        got = f.read(n_frames=2)
        yield lambda: eq(got.coordinates, coordinates[:2])
        yield lambda: eq(got.velocities, None)
        yield lambda: eq(got.alchemicalLambda, np.array([1,2]))


def test_read_slice_1():
    coordinates = np.random.randn(4, 10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates)

    with HDF5TrajectoryFile(temp) as f:
        got = f.read(n_frames=2)
        yield lambda: eq(got.coordinates, coordinates[:2])
        yield lambda: eq(got.velocities, None)

        got = f.read(n_frames=2)
        yield lambda: eq(got.coordinates, coordinates[2:])
        yield lambda: eq(got.velocities, None)


def test_read_slice_2():
    coordinates = np.random.randn(4, 10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates, alchemicalLambda=np.arange(4))

    with HDF5TrajectoryFile(temp) as f:
        got = f.read(atom_indices=np.array([0,1]))
        yield lambda: eq(got.coordinates, coordinates[:, [0,1], :])
        yield lambda: eq(got.alchemicalLambda, np.arange(4))


def test_read_slice_3():
    coordinates = np.random.randn(4, 10,3)
    with HDF5TrajectoryFile(temp, 'w') as f:
        f.write(coordinates, alchemicalLambda=np.arange(4))

    with HDF5TrajectoryFile(temp) as f:
        got = f.read(stride=2, atom_indices=np.array([0,1]))
        yield lambda: eq(got.coordinates, coordinates[::2, [0,1], :])
        yield lambda: eq(got.alchemicalLambda, np.arange(4)[::2])


def test_do_overwrite():
    with open(temp, 'w') as f:
        f.write('a')

    with HDF5TrajectoryFile(temp, 'w', force_overwrite=True) as f:
        f.write(np.random.randn(10,5,3))

@raises(IOError)
def test_do_overwrite():
    with open(temp, 'w') as f:
        f.write('a')

    with HDF5TrajectoryFile(temp, 'w', force_overwrite=False) as f:
        f.write(np.random.randn(10,5,3))
