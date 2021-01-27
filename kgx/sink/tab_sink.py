import os
import tarfile
from typing import Optional, Dict, Set
from ordered_set import OrderedSet

from kgx.sink.sink import Sink
from kgx.utils.kgx_utils import extension_types, archive_write_mode, archive_format, remove_null, _sanitize_export


class TsvSink(Sink):
    """
    TsvSink is responsible for writing data as records
    to a TSV/CSV.
    """

    def __init__(self, filename, format, compression = None, **kwargs):
        super().__init__()
        if format not in extension_types:
            raise Exception(f'Unsupported format: {format}')

        self.delimiter = extension_types[format]
        self.dirname = os.path.abspath(os.path.dirname(filename))
        self.basename = os.path.basename(filename)
        self.extension = format.split(':')[0]
        self.mode = archive_write_mode[compression] if compression in archive_write_mode else None
        self.nodes_file_basename = f"{self.basename}_nodes.{self.extension}"
        self.edges_file_basename = f"{self.basename}_edges.{self.extension}"
        if self.dirname:
            os.makedirs(self.dirname, exist_ok=True)

        self._node_properties = kwargs['node_properties'] if 'node_properties' in kwargs else set()
        self.ordered_node_columns = TsvSink._order_node_columns(self._node_properties)
        self._edge_properties = kwargs['edge_properties'] if 'edge_properties' in kwargs else set()
        self.ordered_edge_columns = TsvSink._order_edge_columns(self._edge_properties)

        self.nodes_file_name = os.path.join(self.dirname if self.dirname else '', self.nodes_file_basename)
        self.NFH = open(self.nodes_file_name, 'w')
        self.NFH.write(self.delimiter.join(self.ordered_node_columns) + '\n')
        self.edges_file_name = os.path.join(self.dirname if self.dirname else '', self.edges_file_basename)
        self.EFH = open(self.edges_file_name, 'w')
        self.EFH.write(self.delimiter.join(self.ordered_edge_columns) + '\n')

    def write_node(self, record) -> None:
        """
        Write a node record to the underlying store.

        Parameters
        ----------
        record: Any
            A node record

        """
        print(record)
        row = self._build_export_row(record)
        row['id'] = record['id']
        values = []
        for c in self.ordered_node_columns:
            if c in row:
                values.append(str(row[c]))
            else:
                values.append("")
        self.NFH.write(self.delimiter.join(values) + '\n')

    def write_edge(self, record):
        """
        Write an edge record to the underlying store.

        Parameters
        ----------
        record: Any
            An edge record

        """
        row = self._build_export_row(record)
        values = []
        for c in self.ordered_edge_columns:
            if c in row:
                values.append(str(row[c]))
            else:
                values.append("")
        self.EFH.write(self.delimiter.join(values) + '\n')

    def finalize(self):
        """
        Create an archive if compression mode is defined.
        """
        if self.mode:
            archive_basename = f"{self.basename}.{archive_format[self.mode]}"
            archive_name = os.path.join(self.dirname if self.dirname else '', archive_basename)
            with tarfile.open(name=archive_name, mode=self.mode) as tar:
                tar.add(self.nodes_file_name, arcname=self.nodes_file_basename)
                tar.add(self.edges_file_name, arcname=self.edges_file_basename)
                if os.path.isfile(self.nodes_file_name):
                    os.remove(self.nodes_file_name)
                if os.path.isfile(self.edges_file_name):
                    os.remove(self.edges_file_name)

    @staticmethod
    def _build_export_row(data: Dict) -> Dict:
        """
        Casts all values to primitive types like str or bool according to the
        specified type in ``_column_types``. Lists become pipe delimited strings.

        Parameters
        ----------
        data: Dict
            A dictionary containing key-value pairs

        Returns
        -------
        Dict
            A dictionary containing processed key-value pairs

        """
        tidy_data = {}
        for key, value in data.items():
            new_value = remove_null(value)
            if new_value:
                tidy_data[key] = _sanitize_export(key, new_value)
        return tidy_data

    @staticmethod
    def _order_node_columns(cols: Set) -> OrderedSet:
        """
        Arrange node columns in a defined order.

        Parameters
        ----------
        cols: Set
            A set with elements in any order

        Returns
        -------
        OrderedSet
            A set with elements in a defined order

        """
        node_columns = cols.copy()
        core_columns = OrderedSet(['id', 'category', 'name', 'description', 'xref', 'provided_by', 'synonym'])
        ordered_columns = OrderedSet()
        for c in core_columns:
            if c in node_columns:
                ordered_columns.add(c)
                node_columns.remove(c)
        internal_columns = set()
        remaining_columns = node_columns.copy()
        for c in node_columns:
            if c.startswith('_'):
                internal_columns.add(c)
                remaining_columns.remove(c)
        ordered_columns.update(sorted(remaining_columns))
        ordered_columns.update(sorted(internal_columns))
        return ordered_columns

    @staticmethod
    def _order_edge_columns(cols: Set) -> OrderedSet:
        """
        Arrange edge columns in a defined order.

        Parameters
        ----------
        cols: Set
            A set with elements in any order

        Returns
        -------
        OrderedSet
            A set with elements in a defined order

        """
        edge_columns = cols.copy()
        core_columns = OrderedSet(['id', 'subject', 'predicate', 'object', 'category', 'relation', 'provided_by'])
        ordered_columns = OrderedSet()
        for c in core_columns:
            if c in edge_columns:
                ordered_columns.add(c)
                edge_columns.remove(c)
        internal_columns = set()
        remaining_columns = edge_columns.copy()
        for c in edge_columns:
            if c.startswith('_'):
                internal_columns.add(c)
                remaining_columns.remove(c)
        ordered_columns.update(sorted(remaining_columns))
        ordered_columns.update(sorted(internal_columns))
        return ordered_columns
