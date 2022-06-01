target = "altera"
syn_tool = "quartus"
action = "synthesis"

# Specific device selection for EP4CE22E22C7
syn_family = "Cyclone IV E"
syn_device = "EP4CE22"
syn_package = "E22C"
syn_grade = "7"

# Uncomment this for JIC generation
# target_memory = "EPCS64"

# Project
syn_top = "lane"
syn_project = "lane"

files = [
    "../../../src/lane_g_matrix.vhd",
    "../../../src/lane_g_root_IP.vhd",
    "../../../src/lane_linemem.vhd",
    "../../../src/lane_sobel.vhd",
    "../../../../FPGA-Vision/FPGA-Design/lane.vhd",
    "../../../../FPGA-Vision/FPGA-Design/lane.sdc",
    "../../../../FPGA-Vision/FPGA-Design/lane_sync.vhd",
]

quartus_preflow = "lane_default_Cyclone_IV.qsf"

# Custom commands
remove_generated_files = "rm -f {}.rpf {}.sld".format(syn_project, syn_project)

# Uncomment this for JIC generation
# memory_file_gen_cmd = "quartus_cpf -c -d {} -s {} {}.sof {}.jic".format(target_memory, syn_device, syn_project, syn_project)

# Toolchain flow pre and post commands
syn_pre_bitstream_cmd = remove_generated_files
# Uncomment this for JIC generation
# syn_post_bitstream_cmd = memory_file_gen_cmd
