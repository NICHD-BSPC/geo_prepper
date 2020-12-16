GEO submission prepper
======================

Submission of high-throughput sequencing data to a public database
such as NCBI GEO (`<https://www.ncbi.nlm.nih.gov/geo/>`_)
is a critical part of the process of disseminating important scientific
advances to the greater community. With the widespread adoption
of high-throughput sequencing and fast-paced development of associated scientific assays, the scope
and complexity of such projects have increased dramatically, to the point
that prominent scientific articles often employ several different sequencing assays to tell
different parts of the story.

NCBI GEO is one of the most widely-used databases of sequencing data. Submissions
will typically include raw data files organized in a particular hierarchy and
a metadata spreadsheet containing details about samples that are part of the
study. The metadata spreadsheet is comprehensive, allowing users to include
arbitrary numbers of samples and metadata. However, filling out this Excel
spreadsheet is tedious and error-prone, as we have to fill in information about
potentially hundreds of samples, with data spread across several different
locations, essentially by hand.

To address this problem, here we present ``geo-prepper``, a tool to automate
parts of the data submission process to NCBI GEO. Given a samplesheet and config file,
the tool symlinks raw data to a desired output location, and automatically generates
files that can be used to populate the GEO sample submission spreadsheet.

Usage
+++++

::

	python __init__.py [-h] [-s SAMPLETABLE] [-c CONFIG] [-o OUTPUT_DIR] [-g GROUPING_COL] [-f]

	  -s/--sampletable SAMPLETABLE
	        Sampletable with sample names, technical replicates (if any), links to raw data and other metadata
	  -c/--config CONFIG
	        Config yaml file that defines columns of interest in sampletable
	  -o/--output_dir OUTPUT_DIR
	        Output directory
	  -g/--grouping_col GROUPING_COL
	        (Optional) Column to group technical replicates. If specified, will override config.yaml specification
	  -f/--force
	        (Optional) Overwrite output directory if it exists


The tool has three required inputs:

1. `config.yaml`_
2. `sampletable`_
3. ``OUTPUT_DIR``: This is the output directory where symlinks to raw data files and other files
   are created (see `Output`_ section). If the specified directory already exists, the tool
   exits with a warning.

In addition, there are two optional parameters:

1. ``GROUPING_COL``: This is a column in the sampletable that is used to group technical replicates.
   If specified, this overrides the ``config.yaml`` specification (see `grouping_col`_ below).
2. ``-f/--force``: If specified, this will overwrite an existing output directory.


**Warning:** File paths specified in the sampletable must be **absolute paths**.

Input
+++++

config.yaml
^^^^^^^^^^^

This is a configuration file with options specified in a yaml format. Here
is a sample ``config.yaml`` for a ChIP-Seq data set:
`link<templates/config-chipseq.yaml>`_

Below we list the accepted parameters
of which `sample_col`_, `is_paired_end`_ and `file_cols`_ are required:

sample_col
----------

This is used to specify the column containing the sample ID.
The value will be used to match the column names in the
sample table.

For example, ``sample_col: samplename`` will look for the column
named *samplename* in the sample table for the sample IDs. The
values in this column must be unique.

is_paired_end
-------------

This is used to specify single-end (SE) or paired-end (PE) data and
must be a boolean (``True`` or ``False``).

file_cols
---------

Here we specify the columns containing files to include in the
GEO submission as ``key:value`` pairs. Accepted keys are listed below:

Note that, all paths must be **absolute paths** to the described files.

+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| key      | description                                                                                                                                                                    |
+==========+================================================================================================================================================================================+
| R1       | **Required** Read 1 file (e.g. ``sample.R1.fastq.gz``) for SE or PE RNA-Seq or ChIP-Seq data, or cellranger BAM file (e.g. ``possorted_genome_bam.bam``) for single-cell data. |
+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| R2       | Read 2 file (e.g. ``sample.R2.fastq.gz``) for PE RNA-Seq or ChIP-Seq data. Required if `is_paired_end`_ is True.                                                               |
+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| peaks    | Peak file (e.g. ``peaks.bed``) output by ChIP-Seq peak caller.                                                                                                                 |
+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| bigwig   | Bigwig file with ChIP-Seq signal                                                                                                                                               |
+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| features | Features TSV file (e.g. ``features.tsv.gz``) output by cellranger for single-cell data.                                                                                        |
+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| barcodes | Barcodes TSV file (e.g. ``barcodes.tsv.gz``) output by cellranger for single-cell data.                                                                                        |
+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| matrix   | Matrix TSV file (e.g. ``matrix.mtx.gz``) output by cellranger for single-cell data                                                                                             |
+----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


**Note:** Of the keys listed above, only ``R1`` is required. As such, any arbitrary keys can
be added in this section to match specific file types that are part of the submission.


metadata_cols
-------------

A bulleted list specifying additional metadata columns in the sample table. For example,

::

    metadata_cols:
        - celltype
        - genotype

will look for the columns ``celltype`` and ``genotype`` in the sampletable and include them in the output
``sample_section.tsv``.

skip_column_suffix
------------------

By default, all keys listed in the `file_cols`_ section, are included as a suffix in the output
(symlinked) file names. So, let's say, in the ``file_cols`` section, we specified,

::

    file_cols:
        R1: 'orig_filename'
        peaks : 'sicer'

and in the sampletable, we have the following lines:

+------------+----------------------------------------+----------------------------------------+
| samplename | orig_filename                          | sicer                                  |
+============+========================================+========================================+
| wt_1       | /data/project/seq_core_237_R1.fastq.gz | /data/project/peakcaller/peaks_237.bed |
+------------+----------------------------------------+----------------------------------------+
| wt_2       | /data/project/seq_core_238_R1.fastq.gz | /data/project/peakcaller/peaks_238.bed |
+------------+----------------------------------------+----------------------------------------+

The output files will be symlinked to the specified output directory (e.g. ``geo_project``) as,

::

    geo_project/
      ├ wt_1_R1.fastq.gz -> /data/project/seq_core_237_R1.fastq.gz
      ├ wt_2_R1.fastq.gz -> /data/project/seq_core_238_R1.fastq.gz
      ├ wt_1_peaks.bed -> /data/project/sicer/peaks_237.bed
      └ wt_2_peaks.bed -> /data/project/sicer/peaks_238.bed

So, the ``key`` in the ``file_cols`` section (e.g. ``peaks``), is included in the file name as
a suffix (``_peaks``). To override this behavior, specify the corresponding columns in
the ``skip_column_suffix`` section, as:

::

    skip_column_suffix:
        - peaks

Now, the peak files don't have the suffix ``_peaks`` in the file name and the
output directory looks like:

::

    geo_project/
      ├ wt_1_R1.fastq.gz -> /data/project/seq_core_237_R1.fastq.gz
      ├ wt_2_R1.fastq.gz -> /data/project/seq_core_238_R1.fastq.gz
      ├ wt_1.bed -> /data/project/sicer/peaks_237.bed
      └ wt_2.bed -> /data/project/sicer/peaks_238.bed

grouping_col
------------

This is used to specify technical replicates (if any). Samples having the same value
in the ``grouping_col`` column, will be considered technical replicates. This is an optional
parameter, and if unspecified, defaults to ``sample_col``.

sampletable
^^^^^^^^^^^

This is a TSV where each row corresponds to an individual sample.

- If the data set contains technical replicates, each *technical replicate* is a sample.
  Otherwise, each *biological replicate* constitutes a sample.
- Column names of this file must correspond to those specified in the `config.yaml`_.
- The sampletable must contain the `sample_col`_ column.
- The sampletable must contain the ``R1`` column from the `file_cols`_ section of the config.yaml.
  If `is_paired_end`_ is ``True``, then the sampletable must also contain the ``R2`` column.
- All paths specified must be **absolute paths**.

Output
++++++

The tool outputs symlinks to the raw or processed files specified in the sample table that
are renamed using the format: ``<sample_col>_<file_cols key>.<extension>``. So, for example, if

- ``samplename`` is ``wt_1``
- extension is ``.fastq.gz``
- `file_cols`_ key is ``R1``

| Then the symlinked output file is ``wt_1_R1.fastq.gz``.
|

**Note:**

The 'extension' is calculated from the raw file name as the string following the first period (.)
in the basename of the file.

- For example, for a file named ``seq_core_237_R1.fastq.gz``, the extension will be ``.fastq.gz``.
- However, if the file is named ``seq_core_237.R1.fastq.gz`` the extension will be ``.R1.fastq.gz``.

In addition, the tool also outputs the following files:

md5hash.tsv
^^^^^^^^^^^

For each file specified in the sampletable, md5 hashes are calculated using the
``md5sum`` utility with a ``subprocess.run`` call and output to a TSV with file names
in the first column and md5 hashes in the second column.

sample_section.tsv
^^^^^^^^^^^^^^^^^^

This is a TSV where each row contains all files corresponding to a particular sample
including metadata columns, technical replicates and processed files if any. This can be used
to populate the ``Sample section`` in the GEO submission template.

paired_end.tsv
^^^^^^^^^^^^^^

This is only output for PE data and lists Read 1 and Read 2 fastq files for each sample
in two columns. This can be used to populate the final ``Paired-end`` section in the
GEO submission template.
