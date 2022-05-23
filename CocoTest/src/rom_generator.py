from csv import reader
from os import environ

HOME = environ['HOME']
REPO_PATH = HOME + '/Documents/Vision-Course'
MIF_FILE = '/FPGA-Vision/FPGA-Design/lane_g_root.mif'
OUT_FILE = '/CocoTest/src/lane_g_root_IP.vhd'
LINES_TO_SCAPE = 5
with open(MIF_FILE, newline='') as csvfile:
    content = reader(csvfile, delimiter='\t')
    i = 0
    add = []
    value = []
    for c in content:
        if i > 5:
            if c[0] == 'END;':
                break
            add.append(int(c[0]))
            value.append(int(c[2]))
        i += 1
bin_add = [format(v, '013b') for v in add]
bin_value = [format(v, '08b') for v in value]

file = open(OUT_FILE, "w")
file.write("-- Custom Vendorless ROM\n")
file.write("\n")
file.write("library ieee;\nuse ieee.std_logic_1164.all;\n")
file.write("\n")
file.write("entity lane_g_root_IP is\nport (\n")
file.write("        address : IN STD_LOGIC_VECTOR (12 DOWNTO 0);\n")
file.write("        clock   : IN STD_LOGIC  := '1';\n")
file.write("        q       : OUT STD_LOGIC_VECTOR (7 DOWNTO 0)\n")
file.write("        );\n")
file.write("end entity lane_g_root_IP;\n")
file.write("\n")
file.write("architecture behavioral of lane_g_root_IP is\n")
file.write("  type mem is array ( 0 to 2**13 - 1) of std_logic_vector(7 downto 0);\n")
file.write("  constant my_Rom : mem := (\n")
for i in range(len(add)-1):
    file.write(f"    {add[i]} => \"{bin_value[i]}\",\n")
file.write(f"    {add[-1]} => \"{bin_value[-1]}\");\n")
file.write("  signal q_unbuf : std_logic_vector(7 downto 0);\n")
file.write("begin\n")
file.write("   process (address)\n")
file.write("   begin\n")
file.write("     case address is\n")
for i in range(len(bin_add)):
    file.write(f"      when \"{bin_add[i]}\" => q_unbuf <= my_rom({i});\n")
file.write("      when others => q_unbuf <= \"00000000\";\n")
file.write("     end case;\n")
file.write("  end process;\n")
file.write("\n")
file.write("  process\n")
file.write("  begin\n")
file.write("    wait until rising_edge(clock);\n")
file.write("    q <= q_unbuf;\n")
file.write("  end process;\n")
file.write("\n")
file.write("end architecture behavioral;\n")
