import numpy as np

OUT_FILE = 'lane_g_root_IP.vhd'

ADDRESS_RANGE = 12
OUTPUT_RANGE = 8

add = list(range(1 << ADDRESS_RANGE))
max_output = (1 << OUTPUT_RANGE) - 1
value = [max_output-np.uint8(np.sqrt(8*a)) for a in add]
bin_add = [format(v, f'0{ADDRESS_RANGE}b') for v in add]
bin_value = [format(v, f'0{OUTPUT_RANGE}b') for v in value]

file = open(OUT_FILE, "w")
file.write("-- Custom Vendorless ROM\n")
file.write("\n")
file.write("library ieee;\nuse ieee.std_logic_1164.all;\n")
file.write("\n")
file.write("entity lane_g_root_IP is\nport (\n")
file.write(f"        address : IN STD_LOGIC_VECTOR ({ADDRESS_RANGE-1} DOWNTO 0);\n")
file.write("        clock   : IN STD_LOGIC  := '1';\n")
file.write(f"        q       : OUT STD_LOGIC_VECTOR ({OUTPUT_RANGE-1} DOWNTO 0)\n")
file.write("        );\n")
file.write("end entity lane_g_root_IP;\n")
file.write("\n")
file.write("architecture behavioral of lane_g_root_IP is\n")
file.write(f"  type mem is array ( 0 to 2**{ADDRESS_RANGE} - 1) of std_logic_vector({OUTPUT_RANGE-1} downto 0);\n")
file.write("  constant my_Rom : mem := (\n")
for i in range(len(add)-1):
    file.write(f"    {add[i]} => \"{bin_value[i]}\",\n")
file.write(f"    {add[-1]} => \"{bin_value[-1]}\");\n")
file.write(f"  signal q_unbuf : std_logic_vector({OUTPUT_RANGE-1} downto 0);\n")
file.write("begin\n")
file.write("   process (address)\n")
file.write("   begin\n")
file.write("     case address is\n")
for i in range(len(bin_add)):
    file.write(f"      when \"{bin_add[i]}\" => q_unbuf <= my_rom({i});\n")
file.write("      when others => q_unbuf <= (others => '1');\n")
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
file.close()
