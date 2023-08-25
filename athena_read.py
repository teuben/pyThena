# Various functions to read Athena++ output data files

# Python modules
import re
import warnings
from io import open  # Consistent binary I/O from Python 2 and 3
import struct

import matplotlib.colors as colors
import matplotlib.patches as patches
import matplotlib.pyplot as plt


# Other Python modules
import numpy as np

check_nan_flag = False


# Check input NumPy array for the presence of any NaN entries
def check_nan(data):
    if np.isnan(data).any():
        raise FloatingPointError("NaN encountered")
    return


# Wrapper to np.loadtxt() for checks used in regression tests
def error_dat(filename, **kwargs):
    data = np.loadtxt(filename,
                      dtype=np.float64,
                      ndmin=2,  # prevent NumPy from squeezing singleton dim
                      **kwargs)
    if check_nan_flag:
        check_nan(data)
    return data


# Read .tab files and return dict.
def tab(filename, show_vars=False):

    # Parse header
    data_dict = {}
    with open(filename, 'r') as data_file:
        line = data_file.readline()
        attributes = re.search(r'time=(\S+)\s+cycle=(\S+)', line)
        line = data_file.readline()
        headings = line.split()[1:]
    headings = headings[1:]

    # Go through lines
    data_array = []
    num_lines = 0
    with open(filename, 'r') as data_file:
        first_line = True
        for line in data_file:
            # Skip comments
            if line.split()[0][0] == '#':
                continue

            # Extract cell indices
            vals = line.split()
            if first_line:
                num_entries = len(vals) - 1
                first_line = False

            # Extract cell values
            vals = vals[1:]
            data_array.append([float(val) for val in vals])
            num_lines += 1

    # Reshape array
    array_shape = (num_lines, num_entries)
    array_transpose = (1, 0)
    data_array = np.transpose(np.reshape(data_array, array_shape),
                              array_transpose)


    
    # Finalize data
    for n, heading in enumerate(headings):
        if check_nan_flag:
            check_nan(data_array[n, ...])
        data_dict[heading] = data_array[n, ...]
    if show_vars:
        return list(data_dict.keys())
    data_dict['time'] = float(attributes.group(1))
    data_dict['cycle'] = int(attributes.group(2))
    return data_dict


# Read .hst files and return dict of 1D arrays.
# Keyword arguments:
# raw -- if True, do not prune file to remove stale data
# from prev runs (default False)
def hst(filename, raw=False):
    # Read data
    with open(filename, 'r') as data_file:
        # Find header
        header_found = False
        multiple_headers = False
        header_location = None
        line = data_file.readline()
        while len(line) > 0:
            if line == '# Athena++ history data\n':
                if header_found:
                    multiple_headers = True
                else:
                    header_found = True
                header_location = data_file.tell()
            line = data_file.readline()
        if multiple_headers:
            warnings.warn('Multiple headers found; using most recent data')
        if header_location is None:
            raise RuntimeError('athena_read.hst: Could not find header')

        # Parse header
        data_file.seek(header_location)
        header = data_file.readline()
        data_names = re.findall(r'\[\d+\]=(\S+)', header)
        if len(data_names) == 0:
            raise RuntimeError('athena_read.hst: Could not parse header')

        # Prepare dictionary of results
        data = {}
        for name in data_names:
            data[name] = []

        # Read data
        for line in data_file:
            for name, val in zip(data_names, line.split()):
                data[name].append(float(val))

    # Finalize data
    for key, val in data.items():
        data[key] = np.array(val)
    if not raw:
        if data_names[0] != 'time':
            raise AthenaError('Cannot remove spurious data because time '
                              'column could not be identified')
        branches_removed = False
        while not branches_removed:
            branches_removed = True
            for n in range(1, len(data['time'])):
                if data['time'][n] <= data['time'][n-1]:
                    branch_index = np.where((data['time'][:n] >=
                                             data['time'][n]))[0][0]
                    for key, val in data.items():
                        data[key] = np.concatenate((val[:branch_index],
                                                    val[n:]))
                    branches_removed = False
                    break
        if check_nan_flag:
            for key, val in data.items():
                check_nan(val)
    return data

# Read .bin files and return dict with numpy array of variables and WCS
# This is a Z-only code ripped from athenak's plot_slice.py
# It returns not only all numpy arrays, but also a few meta-data
# named:   'time', 'xlim', 'ylim'
def bin(filename, show_vars=False, **kwargs):
    
    # Read data
    with open(filename, 'rb') as f:

        # Get file size
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0, 0)

        # Read header metadata
        line = f.readline().decode('ascii')
        if line != 'Athena binary output version=1.1\n':
            print(line)
            raise RuntimeError('Unrecognized data file format.')
        next(f)
        line = f.readline().decode('ascii')
        if line[:7] != '  time=':
            raise RuntimeError('Could not read time.')
        sim_time = float(line[7:])
        next(f)
        line = f.readline().decode('ascii')
        if line[:19] != '  size of location=':
            raise RuntimeError('Could not read location size.')
        location_size = int(line[19:])
        line = f.readline().decode('ascii')
        if line[:19] != '  size of variable=':
            raise RuntimeError('Could not read variable size.')
        variable_size = int(line[19:])
        next(f)
        line = f.readline().decode('ascii')
        if line[:12] != '  variables:':
            raise RuntimeError('Could not read variable names.')
        variable_names_base = line[12:].split()
        line = f.readline().decode('ascii')
        if line[:16] != '  header offset=':
            raise RuntimeError('Could not read header offset.')
        header_offset = int(line[16:])

        # Process header metadata
        if location_size not in (4, 8):
            raise RuntimeError('Only 4- and 8-byte integer types supported for '
                               'location data.')
        location_format = 'f' if location_size == 4 else 'd'
        if variable_size not in (4, 8):
            raise RuntimeError('Only 4- and 8-byte integer types supported for cell '
                               'data.')
        variable_format = 'f' if variable_size == 4 else 'd'
        num_variables_base = len(variable_names_base)
        if show_vars:
            return variable_names_base
            
        if True:
            variable_name = kwargs['variable']
            if variable_name not in variable_names_base:
                raise RuntimeError('Variable "{0}" not found; options are {{{1}}}.'
                                   .format(variable_name,
                                           ', '.join(variable_names_base)))
            variable_names = [variable_name]
            variable_ind = 0
            while variable_names_base[variable_ind] != variable_name:
                variable_ind += 1
            variable_inds = [variable_ind]
        variable_names_sorted = \
            [name for _, name in sorted(zip(variable_inds, variable_names))]
        variable_inds_sorted = \
            [ind for ind, _ in sorted(zip(variable_inds, variable_names))]

        # @todo loop over variables
        retval = {}

        # Read input file metadata
        input_data = {}
        start_of_data = f.tell() + header_offset
        while f.tell() < start_of_data:
            line = f.readline().decode('ascii')
            if line[0] == '#':
                continue
            if line[0] == '<':
                section_name = line[1:-2]
                input_data[section_name] = {}
                continue
            key, val = line.split('=', 1)
            input_data[section_name][key.strip()] = val.split('#', 1)[0].strip()

        # Extract number of ghost cells from input file metadata
        try:
            num_ghost = int(input_data['mesh']['nghost'])
        except:  # noqa: E722
            raise RuntimeError('Unable to find number of ghost cells in input file.')

        # Prepare lists to hold results
        max_level_calculated = -1
        block_loc_for_level = []
        block_ind_for_level = []
        num_blocks_used = 0
        extents = []
        quantities = {}
        for name in variable_names_sorted:
            quantities[name] = []

        # Go through blocks
        first_time = True
        while f.tell() < file_size:

            # Read grid structure data
            block_indices = np.array(struct.unpack('@6i', f.read(24))) - num_ghost
            block_i, block_j, block_k, block_level = struct.unpack('@4i', f.read(16))

            # Process grid structure data
            if first_time:
                block_nx = block_indices[1] - block_indices[0] + 1
                block_ny = block_indices[3] - block_indices[2] + 1
                block_nz = block_indices[5] - block_indices[4] + 1
                cells_per_block = block_nz * block_ny * block_nx
                block_cell_format = '=' + str(cells_per_block) + variable_format
                variable_data_size = cells_per_block * variable_size
                if True:
                    # if kwargs['dimension'] == 'z':
                    if block_nx == 1:
                        raise RuntimeError('Data in file has no extent in x-direction.')
                    if block_ny == 1:
                        raise RuntimeError('Data in file has no extent in y-direction.')
                    block_nx1 = block_nx
                    block_nx2 = block_ny
                    slice_block_n = block_nz
                    slice_location_min = float(input_data['mesh']['x3min'])
                    slice_location_max = float(input_data['mesh']['x3max'])
                    slice_root_blocks = (int(input_data['mesh']['nx3'])
                                         // int(input_data['meshblock']['nx3']))
                slice_normalized_coord = (kwargs['location'] - slice_location_min) \
                    / (slice_location_max - slice_location_min)
                first_time = False

            # Determine if block is needed
            if block_level > max_level_calculated:
                for level in range(max_level_calculated + 1, block_level + 1):
                    if kwargs['location'] <= slice_location_min:
                        block_loc_for_level.append(0)
                        block_ind_for_level.append(0)
                    elif kwargs['location'] >= slice_location_max:
                        block_loc_for_level.append(slice_root_blocks - 1)
                        block_ind_for_level.append(slice_block_n - 1)
                    else:
                        slice_mesh_n = slice_block_n * slice_root_blocks * 2 ** level
                        mesh_ind = int(slice_normalized_coord * slice_mesh_n)
                        block_loc_for_level.append(mesh_ind // slice_block_n)
                        block_ind_for_level.append(mesh_ind - slice_block_n
                                                   * block_loc_for_level[-1])
                max_level_calculated = block_level
            # z
            if block_k != block_loc_for_level[block_level]:
                f.seek(6 * location_size + num_variables_base * variable_data_size, 1)
                continue
            num_blocks_used += 1

            # Read coordinate data
            block_lims = struct.unpack('=6' + location_format, f.read(6 * location_size))
            # z
            extents.append((block_lims[0], block_lims[1], block_lims[2],
                            block_lims[3]))

            # Read cell data
            cell_data_start = f.tell()
            for ind, name in zip(variable_inds_sorted, variable_names_sorted):
                if ind == -1:
                    # z
                    quantities[name].append(np.full((block_ny, block_nx),
                                                    block_level))
                else:
                    f.seek(cell_data_start + ind * variable_data_size, 0)
                    cell_data = (np.array(struct.unpack(block_cell_format,
                                                        f.read(variable_data_size)))
                                 .reshape(block_nz, block_ny, block_nx))
                    block_ind = block_ind_for_level[block_level]
                    # z
                    quantities[name].append(cell_data[block_ind, :, :])
            f.seek((num_variables_base - ind - 1) * variable_data_size, 1)

    # Prepare to calculate derived quantity
    for name in variable_names_sorted:
        quantities[name] = np.array(quantities[name])

    # Extract quantity without derivation
    quantity = quantities[variable_name]

    if kwargs['output_file'] == None:
        if num_blocks_used > 1:
            raise RuntimeError('too many blocks, mesh and meshblock not the same')
        quantities['time'] = sim_time

        x1_min = float(input_data['mesh']['x1min'])
        x1_max = float(input_data['mesh']['x1max'])
        x2_min = float(input_data['mesh']['x2min'])
        x2_max = float(input_data['mesh']['x2max'])
        quantities['xlim'] = (x1_min,x1_max)
        quantities['ylim'] = (x2_min,x2_max)
            
        return quantities

    # Calculate colors
    if kwargs['vmin'] is None:
        vmin = np.nanmin(quantity)
    else:
        vmin = kwargs['vmin']
    if kwargs['vmax'] is None:
        vmax = np.nanmax(quantity)
    else:
        vmax = kwargs['vmax']

    # Choose colormap norm
    if kwargs['norm'] == 'linear':
        norm = colors.Normalize(vmin, vmax)
        vmin = None
        vmax = None
    elif kwargs['norm'] == 'log':
        norm = colors.LogNorm(vmin, vmax)
        vmin = None
        vmax = None
    else:
        norm = kwargs['norm']

    # Prepare figure
    plt.figure()

    x1_labelpad = 2.0
    x2_labelpad = 2.0
    dpi = 300
    
    # Plot data
    for block_num in range(num_blocks_used):
        d = quantity[block_num]
        print("block_num:",block_num,d.shape,extents[block_num])
        
        plt.imshow(quantity[block_num], cmap=kwargs['cmap'], norm=norm, vmin=vmin,
                   vmax=vmax, interpolation='none', origin='lower',
                   extent=extents[block_num])
    # Make colorbar
    plt.colorbar()

    # Adjust axes
    # z
    x1_min = float(input_data['mesh']['x1min'])
    x1_max = float(input_data['mesh']['x1max'])
    x2_min = float(input_data['mesh']['x2min'])
    x2_max = float(input_data['mesh']['x2max'])
    print("Mesh:  X: %g %g    Y: %g %g" % (x1_min,x1_max,x2_min,x2_max))
    if kwargs['x1_min'] is not None:
        x1_min = kwargs['x1_min']
    if kwargs['x1_max'] is not None:
        x1_max = kwargs['x1_max']
    if kwargs['x2_min'] is not None:
        x2_min = kwargs['x2_min']
    if kwargs['x2_max'] is not None:
        x2_max = kwargs['x2_max']
    plt.xlim((x1_min, x1_max))
    plt.ylim((x2_min, x2_max))
    # z
    plt.xlabel('$x$', labelpad=x1_labelpad)
    plt.ylabel('$y$', labelpad=x2_labelpad)
    
    # Adjust layout
    plt.tight_layout()


    # Save or display figure
    if kwargs['output_file'] != 'show':
        plt.savefig(kwargs['output_file'], dpi=dpi)
    else:
        plt.show()


# General exception class for these functions
class AthenaError(RuntimeError):
    pass


# testing the bin function
if __name__ == "__main__":
    import sys
    
    kwargs = {}
    kwargs['variable'] = 'dens'
    kwargs['dimension'] = 'z'
    kwargs['location'] = 0
    kwargs['vmin'] = None
    kwargs['vmax'] = None
    kwargs['norm'] = 'linear'
    kwargs['cmap'] = 'viridis'
    kwargs['x1_min'] = None
    kwargs['x1_max'] = None
    kwargs['x2_min'] = None
    kwargs['x2_max'] = None
    kwargs['x2_max'] = None
    kwargs['output_file'] = 'show'
    # kwargs['output_file'] = None

    if False:
        print(bin(sys.argv[1],True))
        d = bin(sys.argv[1],False,**kwargs)    
        print('data',d)
    else:
        print(tab(sys.argv[1],True))
        d = tab(sys.argv[1],False)
        print('data',d)
        
