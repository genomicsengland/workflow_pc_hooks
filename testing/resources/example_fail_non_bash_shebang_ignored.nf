def summary = [:]

summary['GEL data release'] = params.data_version
summary['Gene input file'] = params.gene_input
summary['Sample input file'] = (params.use_sample_input) ? params.sample_input : 'No user-specified sample file. Default rare disease and cancer germline participants selected.'
summary['Use sample file'] = params.use_sample_input
summary['Output directory'] = params.outdir
// summary['Base directory'] = "${baseDir}"
// summary['Command'] = "${workflow.commandLine}"

println 'GENE VARIANT WORKFLOW'
println '====================='
println summary.collect { k,v -> "${k.padRight(20)}: $v" }.join("\n")
println "\n"


Channel.value(params.data_version).set { ch_data_version }
Channel.fromPath(params.gene_input).set { ch_gene_input }
Channel.fromPath(params.sample_input).set { ch_sample_file }
Channel.of(params.use_sample_input).set {ch_sample_use}

Channel.fromPath(params.excluded_participant_ids).set { ch_excluded_participant_ids }
Channel.value(params.merge_batch_size).set { ch_merge_batch_size }

Channel.value(params.r_container).set { ch_r_container }
Channel.value(params.bcftools_container).set { ch_bcftools_container }
Channel.value(params.vep_container).set { ch_vep_container }

Channel.value(params.genome_build).set { ch_genome_build }

ch_genome_build
    .flatten()
    .merge(Channel.fromPath(params.reference_resources.GRCh37.coord_file)
        .concat(Channel.fromPath(params.reference_resources.GRCh38.coord_file)))
    .set { ch_coord_file }

ch_genome_build
    .flatten()
    .combine(ch_data_version)
    .combine(ch_excluded_participant_ids)
    .combine(ch_sample_use.combine(ch_sample_file))
    .set { ch_sample_input }

ch_genome_build
    .flatten()
    .merge(Channel.fromPath(params.reference_resources.GRCh37.fasta_file)
        .concat(Channel.fromPath(params.reference_resources.GRCh38.fasta_file)))
    .into { ch_fasta_file; ch_fasta_file_annotation }

ch_genome_build
    .flatten()
    .merge(Channel.fromPath(params.reference_resources.GRCh37.vep_config_file)
        .concat(Channel.fromPath(params.reference_resources.GRCh38.vep_config_file)))
    .set { ch_vep_config_file }

ch_genome_build
    .flatten()
    .merge(Channel.fromPath(params.reference_resources.GRCh37.vep_cache)
        .concat(Channel.fromPath(params.reference_resources.GRCh38.vep_cache)))
    .set { ch_vep_cache }

ch_genome_build
    .flatten()
    .merge(Channel.from(params.reference_resources.GRCh37.vep_cache_version)
        .concat(Channel.from(params.reference_resources.GRCh38.vep_cache_version)))
    .set { ch_vep_cache_version }

ch_genome_build
    .flatten()
    .merge(Channel.from(params.reference_resources.GRCh37.vep_cache_synonyms)
        .concat(Channel.from(params.reference_resources.GRCh38.vep_cache_synonyms)))
    .set { ch_vep_cache_synonyms }

// Add plugin/custom files to a list to be made available in the working directory
vep_extra_files_GRCh37 = []
vep_extra_files_GRCh38 = []

if (params.add_clinvar && params.use_loftee) {
    vep_extra_files_GRCh37.add(file(params.reference_resources.GRCh37.clinvar_file, checkIfExists: false))
    vep_extra_files_GRCh37.add(file(params.reference_resources.GRCh37.clinvar_index, checkIfExists: false))
    vep_extra_files_GRCh37.add(file(params.reference_resources.GRCh37.loftee_human_ancestor_fa, checkIfExists: false))
    vep_extra_files_GRCh37.add(file(params.reference_resources.GRCh37.loftee_gerp_file, checkIfExists: false))
    vep_extra_files_GRCh37.add(file(params.reference_resources.GRCh37.loftee_conservation_file, checkIfExists: false))

    vep_extra_files_GRCh38.add(file(params.reference_resources.GRCh38.clinvar_file, checkIfExists: false))
    vep_extra_files_GRCh38.add(file(params.reference_resources.GRCh38.clinvar_index, checkIfExists: false))
    vep_extra_files_GRCh38.add(file(params.reference_resources.GRCh38.loftee_human_ancestor_fa, checkIfExists: false))
    vep_extra_files_GRCh38.add(file(params.reference_resources.GRCh38.loftee_gerp_bigwig, checkIfExists: false))
    vep_extra_files_GRCh38.add(file(params.reference_resources.GRCh38.loftee_conservation_file, checkIfExists: false))
}

ch_genome_build
    .flatten()
    .merge(Channel.from([vep_extra_files_GRCh37, vep_extra_files_GRCh38]))
    .set { ch_vep_extra_files }


// Get coordinates for query genes
process fetch_coords {
    tag "${genome_build}"
    publishDir "${params.outdir}", mode: 'copy'

    input:
    tuple val(genome_build),
        path(coord_file),
        path(gene_input) from ch_coord_file.combine(ch_gene_input)

    output:
    path("*_coordinates.tsv") into ch_gene_coordinates
    path('versions.yml') into ch_versions_fetch_coords
    path("*_genes_not_found.txt")

    script:
    """
    fetch_coords.R \
    --gene-input ${gene_input} \
    --coord-file ${coord_file} \
    --genome-build ${genome_build}

    cat <<-EOF > versions.yml
    "${task.process}":
      R: \$( R --version | head -n1 | cut -d' ' -f3 )
    EOF
    """
}

// Get build, region, ID information for each gene
ch_gene_coordinates
    .flatten()
    .splitCsv(header: ['build', 'chr', 'start', 'end', 'gene', 'ensemblID', 'internalID', 'posTag', 'originalInput', 'entryDuplicate'], sep: '\t')
    .map { it -> [it.build, it.chr + ':' + it.start + '-' + it.end, it.gene, it.ensemblID, it.originalInput]}
    .set { ch_gene_coordinates }


// Get sample VCF list
process fetch_samples {
    tag "${genome_build}"
    publishDir "${params.outdir}", mode: 'copy'

    input:
    tuple val(genome_build),
        val(data_version),
        path(excluded_participant_ids),
        val(use_sample_input),
        path(sample_input) from ch_sample_input

    output:
    path("*_germline_input_vcfs.txt") into ch_sample_vcfs
    path('versions.yml') into ch_versions_fetch_samples

    script:
    """
    set -eou pipefail

    if [ ${use_sample_input} = true ]
    then
        grep ${genome_build} ${sample_input} > ${genome_build}_germline_input_vcfs.txt || true
    else
        fetch_samples.R \
        --data-version ${data_version} \
        --genome-build '${genome_build}' \
        --excluded-participant-ids ${excluded_participant_ids}
    fi

    cat <<-EOF > versions.yml
    "${task.process}":
      R: \$( R --version | head -n1 | cut -d' ' -f3 )
    EOF
    """
}

// Parse VCF paths and split files
ch_sample_vcfs
    .splitCsv(header: ['participant_id', 'platekey', 'genome_build', 'file_path'], sep: '\t')
    .map { it -> [it.participant_id, it.platekey, it.genome_build, file(it.file_path, checkIfExists: false)] }
    .collectFile() { it ->
        [ "${it[2]}_germline_input_vcfs.txt", it[0] + '\t' + it[1]+ '\t' + it[2] + '\t' + it[3] + '\n' ]
    }
    .map { it -> [it.baseName.split('_')[0], it]}
    .splitText(by: params.merge_batch_size, file: 'split')
    .set { ch_split_files }


// Combine chunks and coordinates
ch_gene_coordinates
    .combine(ch_split_files, by: 0)
    .set { ch_combined_regions_splits }


// Merge VCFs by chunk selecting query genes regions
process first_round_merge {
    tag "${build}, ${region}, ${split_file}"

    input:
    tuple val(build),
        val(region),
        val(gene),
        val(ensemblID),
        val(originalInput),
        path(split_file) from ch_combined_regions_splits

    output:
    tuple val(build),
        val(gene),
        val(ensemblID),
        val(originalInput),
        path("*_first_round_merge.bcf") into ch_first_round_merge
    path('versions.yml') into ch_versions_first_round_merge

    script:
    """
    set -eou pipefail

    file=\$(basename -- "${split_file}")
    extension="\${file##*.}"
    prefix="\${file%.*}"

    awk '{print \$4}' ${split_file} > vcf.list

    bcftools merge \
    --apply-filters PASS \
    --file-list vcf.list \
    --merge both \
    --regions ${region} \
    | bcftools annotate \
    --remove FORMAT/PL \
    -Ob -o \${prefix}_first_round_merge.bcf

    bcftools index \
    --csi \${prefix}_first_round_merge.bcf

    cat <<-EOF > versions.yml
    "${task.process}":
      bcftools: \$(bcftools --version 2>&1 | head -n1 | sed 's/^.bcftools //; s/ .\$//')
    EOF
    """
}

// Combine build, fasta file, merge file list
ch_first_round_merge
    .groupTuple(by: [0, 1, 2, 3])
    .combine(ch_fasta_file, by: 0)
    .set { ch_combined_fasta_merge_list }


// Merge and norm to multi-sample VCF
process second_round_merge {
    tag "${gene}, ${build}"
    publishDir "${params.outdir}", mode: 'copy'

    input:
    tuple val(build),
        val(gene),
        val(ensemblID),
        val(originalInput),
        val(chunks),
        path(reference_fasta) from ch_combined_fasta_merge_list

    output:
    tuple val(build),
        val(gene),
        val(ensemblID),
        val(originalInput),
        path("${build}_merged_normalized.bcf"),
        path("${build}_merged_normalized.bcf.csi") into ch_merged_normalized
    path('versions.yml') into ch_versions_second_round_merge

    script:
    """
    set -eou pipefail

    echo '${chunks}' \
    | sed -e 's/, /\\n/g; s/\\[//; s/\\]//' > chunk.list

    bcftools merge \
    --file-list chunk.list \
    --merge both \
    | bcftools norm --fasta-ref ${reference_fasta} -m-both \
    | bcftools norm --fasta-ref ${reference_fasta} -m+both \
    | bcftools norm --fasta-ref ${reference_fasta} -m-both \
    -Ob -o ${build}_merged_normalized_1.bcf

    bcftools query \
    --format '%CHROM\\t%POS\\t%REF\\t%ALT\\n' ${build}_merged_normalized_1.bcf > test_out

    echo -e "#CHROM\\tPOS\\tREF\\tALT\\tID" > annot.txt
    awk -F"\\t" '{print \$0"\\t"\$1"_"\$2"_"NR}' test_out >> annot.txt
    sort -k2 -n annot.txt > annot_sorted.txt
    bgzip annot_sorted.txt
    tabix -s1 -b2 -e2 annot_sorted.txt.gz

    bcftools annotate ${build}_merged_normalized_1.bcf \
    --remove INFO \
    --columns CHROM,POS,REF,ALT,ID \
    --annotations annot_sorted.txt.gz \
    -Ob -o ${build}_merged_normalized.bcf

    bcftools index \
    --csi ${build}_merged_normalized.bcf

    cat <<-EOF > versions.yml
    "${task.process}":
      bcftools: \$(bcftools --version 2>&1 | head -n1 | sed 's/^.bcftools //; s/ .\$//')
      tabix: \$(echo \$(tabix -h 2>&1) | sed 's/^.*Version: //; s/ .*\$//')
    EOF
    """
}


// Compute and fill VCF INFO tags
process fill_tags_query {
    tag "${gene}, ${build}"

    input:
    tuple val(build),
        val(gene),
        val(ensemblID),
        val(originalInput),
        path(merged_normalized_bcf),
        path(merged_normalized_bcf_index) from ch_merged_normalized

    output:
    tuple val(build),
        val(gene),
        val(ensemblID),
        val(originalInput),
        path("${build}_left_norm_tagged.vcf.gz"),
        path("${build}_left_norm_tagged.vcf.gz.tbi"),
        path("${build}_left_norm_tagged_summary.tsv"),
        path("${build}_left_norm_tagged_het.tsv"),
        path("${build}_left_norm_tagged_hom.tsv"),
        path("${build}_left_norm_tagged_hemi.tsv") into ch_left_norm_tagged
    path('versions.yml') into ch_versions_fill_tags_query

    script:
    """
    set -eou pipefail

    bcftools +fill-tags ${merged_normalized_bcf} -- -t AN,AC,AC_Hom,AC_Het,AC_Hemi,NS \
    | bcftools +missing2ref \
    | bcftools +fill-tags -- -t MAF \
    | bcftools view -Oz -o ${build}_left_norm_tagged.vcf.gz

    bcftools index -t ${build}_left_norm_tagged.vcf.gz

    bcftools query -f '%CHROM\\t%POS\\t%ID\\t%REF\\t%ALT\\t%INFO/AN\\t%INFO/AC\\t%INFO/AC_Hom\\t%INFO/AC_Het\\t%INFO/AC_Hemi\\t%INFO/MAF\\t%INFO/NS\\n' ${build}_left_norm_tagged.vcf.gz > ${build}_left_norm_tagged_summary.tsv
    bcftools query -f '%ID\\t[%SAMPLE,]\\n' -i 'GT="het"' ${build}_left_norm_tagged.vcf.gz > ${build}_left_norm_tagged_het.tsv
    bcftools query -f '%ID\\t[%SAMPLE,]\\n' -i 'GT="AA"' ${build}_left_norm_tagged.vcf.gz > ${build}_left_norm_tagged_hom.tsv
    bcftools query -f '%ID\\t[%SAMPLE,]\\n' -i 'GT="A"' ${build}_left_norm_tagged.vcf.gz > ${build}_left_norm_tagged_hemi.tsv

    cat <<-EOF > versions.yml
    "${task.process}":
      bcftools: \$(bcftools --version 2>&1 | head -n1 | sed 's/^.bcftools //; s/ .\$//')
    EOF
    """
}

// Combine inputs by build
ch_left_norm_tagged
    .combine(ch_fasta_file_annotation, by: 0)
    .combine(ch_vep_config_file, by: 0)
    .combine(ch_vep_cache_version, by: 0)
    .combine(ch_vep_cache, by: 0)
    .combine(ch_vep_cache_synonyms, by: 0)
    .combine(ch_vep_extra_files, by: 0)
    .set { ch_combined_vcf_loftee_fasta_vep }


// VEP-annotate variants
process annotate {
    tag "${gene}, ${build}"

    input:
    tuple val(build),
        val(gene),
        val(ensemblID),
        val(originalInput),
        path(left_norm_tagged_vcf),
        path(left_norm_tagged_vcf_index),
        path(left_norm_tagged_summary),
        path(left_norm_tagged_het),
        path(left_norm_tagged_hom),
        path(left_norm_tagged_hemi),
        path(reference_fasta_file),
        path(vep_config_file),
        val(vep_cache_version),
        path(vep_cache),
        path(vep_cache_synonyms),
        path(clinvar_file),
        path(clinvar_index),
        path(human_ancestor_fa_file),
        path(gerp_file),
        path(conservation_file) from ch_combined_vcf_loftee_fasta_vep

    output:
    tuple val(build),
        val(gene),
        val(ensemblID),
        val(originalInput),
        path(left_norm_tagged_summary),
        path(left_norm_tagged_het),
        path(left_norm_tagged_hom),
        path(left_norm_tagged_hemi),
        path("${build}_left_norm_tagged_annotated.tsv") into ch_annotated_variants
    path('versions.yml') into ch_versions_annotate

    script:
    def args = "${build}" == "GRCh37" ? task.ext.arg.GRCh37 : task.ext.arg.GRCh38

    """
    set -eou pipefail

    export PERL5LIB=\$PERL5LIB:/opt/vep/.vep/Plugins:/opt/vep/.vep/Plugins/loftee-${build}

    vep \
    --input_file ${left_norm_tagged_summary} \
    --output_file ${build}_left_norm_tagged_annotated.tsv \
    --warning_file ${build}_left_norm_tagged_warnings.tsv \
    --format vcf \
    --tab \
    --fork 4 \
    --offline \
    --cache \
    --dir_cache ${vep_cache} \
    --cache_version ${vep_cache_version} \
    --species homo_sapiens \
    --assembly ${build} \
    --fasta ${reference_fasta_file} \
    --config ${vep_config_file} \
    --synonyms ${vep_cache_synonyms} \
    ${args} \
    --no_stats \
    --check_existing \
    --force_overwrite

    cat <<-EOF > versions.yml
    "${task.process}":
      VEP:
    \$(vep -help | grep ^[[:space:]]*ensembl | sed 's/^\\s\\+/    \\- /')
    EOF
    """
}


// Combine +fill-tags summary and VEP annotation
process sum_and_annotate {
    tag "${gene} ${build} variants"
    publishDir "${params.outdir}", mode: 'copy'

    input:
    tuple val(build),
        val(gene),
        val(ensemblID),
        val(originalInput),
        path(left_norm_tagged_summary),
        path(left_norm_tagged_het),
        path(left_norm_tagged_hom),
        path(left_norm_tagged_hemi),
        path(left_norm_tagged_annotated) from ch_annotated_variants

    output:
    path("*_annotated_variants.tsv")
    path('versions.yml') into ch_versions_sum_and_annotate

    script:
    """
    set -eou pipefail

    sum_and_annotate.R \
    --genome-build ${build} \
    --hgnc-symbol ${gene} \
    --ensembl-id ${ensemblID} \
    --original-input ${originalInput} \
    --fill-tags-summary ${left_norm_tagged_summary} \
    --fill-tags-het ${left_norm_tagged_het} \
    --fill-tags-hom ${left_norm_tagged_hom} \
    --fill-tags-hemi ${left_norm_tagged_hemi} \
    --vep-annotation ${left_norm_tagged_annotated}

    cat <<-EOF > versions.yml
    "${task.process}":
      R: \$( R --version | head -n1 | cut -d' ' -f3 )
    EOF
    """
}

ch_versions_fetch_coords.first()
    .mix(
        ch_versions_fetch_samples.first(),
        ch_versions_first_round_merge.first(),
        ch_versions_second_round_merge.first(),
        ch_versions_fill_tags_query.first(),
        ch_versions_annotate.first(),
        ch_versions_sum_and_annotate.first()
    )
    .set { ch_versions }


process dump_versions {
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path(versions) from ch_versions.collectFile(name: 'collated_versions.yml')

    output:
    path "software_versions.yml"

    script:
    //ignore: detect-non-bash-shebangs
    """
    #!/bin/python
    dump_versions.py \
    --versions ${versions} \
    --command "Command:\n${workflow.commandLine}\n" \
    --out software_versions.yml
    """
}
