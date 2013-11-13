password_count = 0
def check():
    global final_token, final_plugins, password_count
    copylines = False
    nsc_cfg = file("NSC.ini")
    for line in nsc_cfg:
        if "password=" in line and password_count != 3:
            password_count += 1
        if "password=" in line and password_count == 3:
            password_count += 1
            store_line = line
            final_token = store_line[9:]
        if "[External Scripts]" in line:
            copylines = False
            store_line = store_line.replace("%SCRIPT%", "$plugin_name")
            store_line = store_line.replace("%ARGS%", "$plugin_args")
            final_plugins = store_line
        
        if copylines == True:
            if "=" in line:
                store_line += ".%s" % line
        
        if "[Script Wrappings]" in line:
            copylines = True
            store_line = ""
            
check()

s = open("ncpa_template.txt").read()
s = s.replace("{token}", final_token.strip())
s = s.replace("{plugins}", final_plugins)
ncpa = open("ncpa.cfg", "w")
ncpa.write(s)

ncpa.close()






